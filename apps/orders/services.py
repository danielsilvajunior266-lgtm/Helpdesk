from django.db import transaction
from django.utils import timezone
from apps.orders.models import ServiceOrder

def start_service_order(order: ServiceOrder, assigned_to=None) -> ServiceOrder:
    with transaction.atomic():
        order.status = 'in_progress'
        order.started_at = timezone.now()
        if assigned_to:
            order.assigned_to = assigned_to
        order.save()
        return order


def complete_service_order(order: ServiceOrder, payment_method: str = None) -> ServiceOrder:
    with transaction.atomic():
        order.status = 'completed'
        order.completed_at = timezone.now()
        if payment_method:
            order.payment_method = payment_method

        is_monthly = (order.customer.billing_type == 'monthly')
        if is_monthly:
            order.billing_status = 'PENDING'
            order.payment_method = 'monthly_invoice'
        else:
            order.billing_status = 'NOT_APPLICABLE'
            # Lazy import para evitar ciclos de importação
            from apps.finance.services import create_cash_entry_from_order
            create_cash_entry_from_order(order)

        order.save()

        # Concessão de fidelidade (se ativo no plano)
        from apps.loyalty.services import process_order_loyalty
        process_order_loyalty(order)

        # Cálculo de comissão para o operador responsável
        from apps.commissions.services import calculate_order_commission
        calculate_order_commission(order)

        return order


def deliver_service_order(order: ServiceOrder) -> ServiceOrder:
    with transaction.atomic():
        order.status = 'delivered'
        order.delivered_at = timezone.now()
        order.save()
        return order


def cancel_service_order(order: ServiceOrder) -> ServiceOrder:
    with transaction.atomic():
        order.status = 'cancelled'
        order.save()

        from apps.finance.services import revert_cash_entry_for_order
        revert_cash_entry_for_order(order)

        from apps.loyalty.services import revert_order_loyalty
        revert_order_loyalty(order)

        from apps.commissions.services import revert_order_commission
        revert_order_commission(order)

        return order


def get_user_service_orders(user, company=None):
    """
    Recupera todas as ordens de serviço vinculadas ao motorista (User), considerando:
    1. Vinculação direta do Customer ao User (customer__user=user)
    2. Veículos do motorista (vehicle__customer__user=user ou placas dos veículos do motorista)
    3. E-mail ou telefone do motorista correspondentes ao cadastro de cliente
    Também realiza auto-sync de Customer records correspondentes.
    """
    from apps.customers.models import Customer, Vehicle
    from django.db.models import Q

    if not user or not user.is_authenticated:
        return ServiceOrder.objects.none()

    # Auto-link Customer profiles que tenham o mesmo email ou telefone mas estavam com user=None
    if user.email:
        Customer.objects.filter(user__isnull=True, email__iexact=user.email).update(user=user)
    if getattr(user, 'phone', None) and user.phone:
        Customer.objects.filter(user__isnull=True, phone=user.phone).update(user=user)

    user_vehicle_plates = list(Vehicle.objects.filter(
        Q(customer__user=user) | Q(customer__email__iexact=user.email if user.email else '---')
    ).values_list('plate', flat=True))

    q_filter = Q(customer__user=user) | Q(vehicle__customer__user=user)
    if user_vehicle_plates:
        q_filter |= Q(vehicle__plate__in=user_vehicle_plates)
    if user.email:
        q_filter |= Q(customer__email__iexact=user.email)
    if getattr(user, 'phone', None) and user.phone:
        q_filter |= Q(customer__phone=user.phone)

    qs = ServiceOrder.objects.filter(q_filter)
    if company:
        qs = qs.filter(company=company)

    return qs.select_related('company', 'vehicle', 'service_type', 'customer', 'assigned_to').prefetch_related('photos').distinct().order_by('-created_at')
