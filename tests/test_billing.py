import pytest
from decimal import Decimal
from apps.orders.models import ServiceOrder
from apps.orders.services import complete_service_order
from apps.billing.services import generate_monthly_invoice, mark_invoice_paid
from apps.finance.models import CashEntry

@pytest.mark.django_db
def test_fleet_monthly_billing_lifecycle(company_a, customer_fleet, vehicle_fleet, service_wash):
    # Cria 2 ordens para o frotista
    order1 = ServiceOrder.objects.create(
        company=company_a,
        customer=customer_fleet,
        vehicle=vehicle_fleet,
        service_type=service_wash,
        price=Decimal('50.00'),
        final_price=Decimal('50.00'),
        status='in_progress'
    )
    complete_service_order(order1)

    order2 = ServiceOrder.objects.create(
        company=company_a,
        customer=customer_fleet,
        vehicle=vehicle_fleet,
        service_type=service_wash,
        price=Decimal('70.00'),
        final_price=Decimal('70.00'),
        status='in_progress'
    )
    complete_service_order(order2)

    assert order1.billing_status == 'PENDING'
    assert order2.billing_status == 'PENDING'

    # Consolida fatura mensal
    invoice = generate_monthly_invoice(company_a, customer_fleet, year=2026, month=9)

    assert invoice.total_amount == Decimal('120.00')
    assert invoice.status == 'open'
    assert invoice.items.count() == 2

    # As ordens devem agora estar marcadas como INVOICED
    order1.refresh_from_db()
    order2.refresh_from_db()
    assert order1.billing_status == 'INVOICED'
    assert order2.billing_status == 'INVOICED'

    # Baixa da fatura
    mark_invoice_paid(invoice, payment_method='pix')

    invoice.refresh_from_db()
    order1.refresh_from_db()
    order2.refresh_from_db()

    assert invoice.status == 'paid'
    assert order1.billing_status == 'PAID'
    assert order2.billing_status == 'PAID'

    # Deve ter gerado receita consolidada de R$ 120.00 no Livro Caixa
    entry = CashEntry.objects.filter(company=company_a, amount=Decimal('120.00'), entry_type='income').first()
    assert entry is not None
