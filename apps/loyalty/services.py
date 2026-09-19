from django.db import transaction
from apps.loyalty.models import LoyaltyAccount, LoyaltyEvent

def process_order_loyalty(order):
    """
    Concede pontos de fidelidade para o cliente da ordem se a empresa tiver o recurso ativo no plano.
    """
    if not order.company.has_feature('loyalty'):
        return None

    if not order.service_type or not order.service_type.counts_for_loyalty:
        return None

    points = order.service_type.loyalty_points_earned or 10
    if points <= 0:
        return None

    with transaction.atomic():
        existing = LoyaltyEvent.objects.filter(company=order.company, order=order, event_type='earned').first()
        if existing:
            return existing

        account, _ = LoyaltyAccount.objects.select_for_update().get_or_create(
            company=order.company,
            customer=order.customer,
            defaults={'points_balance': 0, 'total_points_earned': 0}
        )

        account.points_balance += points
        account.total_points_earned += points
        account.save()

        event = LoyaltyEvent.objects.create(
            company=order.company,
            account=account,
            event_type='earned',
            points=points,
            order=order,
            description=f"Pontos pelo Serviço nº {order.id} - {order.service_type.name}"
        )
        return event


def revert_order_loyalty(order):
    """
    Estorna pontos concedidos anteriormente em caso de cancelamento da ordem.
    """
    if not order.company.has_feature('loyalty'):
        return None

    with transaction.atomic():
        events = LoyaltyEvent.objects.filter(company=order.company, order=order, event_type='earned')
        for ev in events:
            account = LoyaltyAccount.objects.select_for_update().get(id=ev.account_id)
            reversal_points = -ev.points
            account.points_balance = max(0, account.points_balance + reversal_points)
            account.save()

            LoyaltyEvent.objects.create(
                company=order.company,
                account=account,
                event_type='reversed',
                points=reversal_points,
                order=order,
                description=f"Estorno do Serviço nº {order.id} cancelado"
            )
