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

    # Deve ter gerado receita consolidada de R$ 120.00 no Fluxo de Caixa
    entry = CashEntry.objects.filter(company=company_a, amount=Decimal('120.00'), entry_type='income').first()
    assert entry is not None


@pytest.mark.django_db
def test_add_and_remove_fleet_customer(auth_client, company_a, customer_retail):
    from django.urls import reverse
    from apps.customers.models import Customer

    # 1. Promove cliente avulso para frotista
    assert customer_retail.billing_type == 'per_service'
    res = auth_client.post(reverse('billing:add_customer'), {'customer_id': customer_retail.id})
    assert res.status_code == 302

    customer_retail.refresh_from_db()
    assert customer_retail.billing_type == 'monthly'

    # 2. Reverte frotista para avulso
    res2 = auth_client.post(reverse('billing:remove_customer', kwargs={'customer_id': customer_retail.id}))
    assert res2.status_code == 302

    customer_retail.refresh_from_db()
    assert customer_retail.billing_type == 'per_service'


@pytest.mark.django_db
def test_fleet_customer_unbilled_notification(auth_client, company_a, customer_fleet, vehicle_fleet, service_wash):
    from apps.orders.models import ServiceOrder
    from apps.orders.services import complete_service_order

    # Cria ordem de serviço concluída para o frotista
    order = ServiceOrder.objects.create(
        company=company_a,
        customer=customer_fleet,
        vehicle=vehicle_fleet,
        service_type=service_wash,
        price=Decimal('80.00'),
        final_price=Decimal('80.00'),
        status='in_progress'
    )
    complete_service_order(order)
    assert order.billing_status == 'PENDING'

    # Carrega página principal e verifica notificação de cobrança
    res = auth_client.get('/')
    assert res.status_code == 200
    notifs = res.context['notifications']
    fleet_notifs = [n for n in notifs if n['type'] == 'fleet_billing_due']
    assert len(fleet_notifs) == 1
    assert customer_fleet.name in fleet_notifs[0]['title']
    assert '80.00' in fleet_notifs[0]['message']
    assert vehicle_fleet.plate in fleet_notifs[0]['message']


