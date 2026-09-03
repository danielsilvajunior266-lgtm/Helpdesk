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
