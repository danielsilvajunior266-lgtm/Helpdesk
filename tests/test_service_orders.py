import pytest
from decimal import Decimal
from apps.orders.models import ServiceOrder
from apps.orders.services import complete_service_order, cancel_service_order
from apps.finance.models import CashEntry
from apps.loyalty.models import LoyaltyAccount, LoyaltyEvent

@pytest.mark.django_db
def test_complete_retail_order_creates_cash_entry_and_loyalty(company_a, customer_retail, vehicle_retail, service_wash):
    order = ServiceOrder.objects.create(
        company=company_a,
        customer=customer_retail,
        vehicle=vehicle_retail,
        service_type=service_wash,
        price=Decimal('50.00'),
        final_price=Decimal('50.00'),
        status='in_progress'
    )

    completed = complete_service_order(order, payment_method='pix')

    assert completed.status == 'completed'
    assert completed.completed_at is not None
    assert completed.billing_status == 'NOT_APPLICABLE'

    # Deve ter gerado entrada no Livro Caixa
    entry = CashEntry.objects.filter(company=company_a, order=completed).first()
    assert entry is not None
    assert entry.amount == Decimal('50.00')
    assert entry.entry_type == 'income'
    assert entry.payment_method == 'pix'

    # Empresa A tem plano Premium (has_loyalty=True), deve ter acumulado pontos
    account = LoyaltyAccount.objects.filter(company=company_a, customer=customer_retail).first()
    assert account is not None
    assert account.points_balance == 15


@pytest.mark.django_db
def test_complete_fleet_order_sets_billing_status_pending_without_direct_cash(company_a, customer_fleet, vehicle_fleet, service_wash):
    order = ServiceOrder.objects.create(
        company=company_a,
        customer=customer_fleet,
        vehicle=vehicle_fleet,
        service_type=service_wash,
        price=Decimal('50.00'),
        final_price=Decimal('50.00'),
        status='in_progress'
    )

    completed = complete_service_order(order)

    assert completed.status == 'completed'
    assert completed.billing_status == 'PENDING'
    assert completed.payment_method == 'monthly_invoice'

    # NÃO deve gerar entrada direta no caixa no dia do serviço (vai ser faturado depois)
    entry = CashEntry.objects.filter(company=company_a, order=completed).first()
    assert entry is None


@pytest.mark.django_db
def test_cancel_order_reverts_cash_and_loyalty(company_a, customer_retail, vehicle_retail, service_wash):
    order = ServiceOrder.objects.create(
        company=company_a,
        customer=customer_retail,
        vehicle=vehicle_retail,
        service_type=service_wash,
        price=Decimal('50.00'),
        final_price=Decimal('50.00'),
        status='in_progress'
    )

    completed = complete_service_order(order, payment_method='pix')
    assert CashEntry.objects.filter(company=company_a, order=completed).exists()

    # Cancela
    cancelled = cancel_service_order(completed)
    assert cancelled.status == 'cancelled'

    # Entrada de caixa deve ter sido revertida
    assert not CashEntry.objects.filter(company=company_a, order=completed).exists()

    # Saldo de fidelidade deve ter sido estornado
    account = LoyaltyAccount.objects.get(company=company_a, customer=customer_retail)
    assert account.points_balance == 0
