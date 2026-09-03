from django.db import transaction
from django.utils import timezone
from apps.commissions.models import CommissionRule, EmployeeCommission

def calculate_order_commission(order):
    """
    Calcula e provisiona a comissão do funcionário vinculado à ordem de serviço concluída.
    """
    if not order.company.has_feature('commissions'):
        return None

    if not order.assigned_to:
        return None

    rule = CommissionRule.objects.filter(company=order.company, service_type=order.service_type).first()
    if not rule:
        return None

    with transaction.atomic():
        if rule.calc_type == 'percentage':
            amount = (order.final_price * rule.value) / 100
        else:
            amount = rule.value

        if amount <= 0:
            return None

        commission, _ = EmployeeCommission.objects.update_or_create(
            company=order.company,
            order=order,
            defaults={
                'employee': order.assigned_to,
                'amount': amount,
                'status': 'pending'
            }
        )
        return commission


def revert_order_commission(order):
    """
    Remove ou cancela a comissão caso a ordem de serviço seja cancelada.
    """
    if not order.company.has_feature('commissions'):
        return None

    with transaction.atomic():
        EmployeeCommission.objects.filter(company=order.company, order=order).delete()


def pay_commission(commission: EmployeeCommission):
    """
    Marca a comissão como paga ao operador.
    """
    with transaction.atomic():
        commission.status = 'paid'
        commission.paid_at = timezone.now()
        commission.save()
        return commission
