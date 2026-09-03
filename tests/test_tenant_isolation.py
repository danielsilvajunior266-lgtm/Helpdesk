import pytest
from apps.customers.models import Customer, Vehicle
from apps.orders.models import ServiceOrder
from decimal import Decimal

@pytest.mark.django_db
def test_tenant_isolation_between_companies(company_a, company_b, customer_retail, vehicle_retail, service_wash):
    # Cliente na Empresa A
    assert customer_retail.company == company_a

    # Cria cliente na Empresa B
    cust_b = Customer.objects.create(
        company=company_b,
        name='Cliente Exclusivo B',
        phone='11911112222',
        billing_type='per_service'
    )

    # Manager filter por empresa deve isolar os registros
    customers_a = Customer.objects.filter(company=company_a)
    customers_b = Customer.objects.filter(company=company_b)

    assert customer_retail in customers_a
    assert cust_b not in customers_a

    assert cust_b in customers_b
    assert customer_retail not in customers_b


@pytest.mark.django_db
def test_same_plate_allowed_in_different_tenants(company_a, company_b, customer_retail):
    # Cria cliente na Empresa B
    cust_b = Customer.objects.create(company=company_b, name='Cliente B', phone='11911112222')

    # Cria veículo na Empresa A com placa ABC1234
    v_a = Vehicle.objects.create(company=company_a, customer=customer_retail, plate='ABC1234', brand='VW', model='Gol')
    
    # A mesma placa ABC1234 DEVE ser permitida na Empresa B (unique_together = ('company', 'plate'))
    v_b = Vehicle.objects.create(company=company_b, customer=cust_b, plate='ABC1234', brand='VW', model='Gol')

    assert v_a.id != v_b.id
    assert v_a.plate == v_b.plate
    assert v_a.company != v_b.company
