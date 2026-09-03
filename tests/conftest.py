import pytest
from decimal import Decimal
from apps.saas_core.models import Plan, Company
from apps.accounts.models import User
from apps.customers.models import Customer, Vehicle
from apps.services.models import ServiceCategory, ServiceType
from rest_framework.test import APIClient

@pytest.fixture
def basic_plan(db):
    return Plan.objects.create(
        code='basic',
        name='Básico',
        monthly_price=Decimal('39.90'),
        has_loyalty=False,
        has_monthly_billing=False,
        has_inspections=False
    )

@pytest.fixture
def pro_plan(db):
    return Plan.objects.create(
        code='pro',
        name='Pro',
        monthly_price=Decimal('79.90'),
        has_loyalty=True,
        has_monthly_billing=True,
        has_inspections=False
    )

@pytest.fixture
def premium_plan(db):
    return Plan.objects.create(
        code='premium',
        name='Premium',
        monthly_price=Decimal('139.90'),
        has_loyalty=True,
        has_monthly_billing=True,
        has_inspections=True,
        has_commissions=True
    )

@pytest.fixture
def company_a(db, premium_plan):
    return Company.objects.create(
        name='Lava Jato A',
        slug='lava-jato-a',
        plan=premium_plan,
        status='active'
    )

@pytest.fixture
def company_b(db, basic_plan):
    return Company.objects.create(
        name='Lava Jato B',
        slug='lava-jato-b',
        plan=basic_plan,
        status='active'
    )

@pytest.fixture
def owner_user(db, company_a):
    user = User.objects.create_user(
        email='dono.a@teste.com',
        username='dono_a',
        role='owner',
        company=company_a
    )
    user.set_password('senha123')
    user.save()
    return user

@pytest.fixture
def customer_retail(db, company_a):
    return Customer.objects.create(
        company=company_a,
        name='Cliente Avulso',
        phone='11999990001',
        billing_type='per_service'
    )

@pytest.fixture
def customer_fleet(db, company_a):
    return Customer.objects.create(
        company=company_a,
        name='Cliente Frota',
        phone='11999990002',
        billing_type='monthly'
    )

@pytest.fixture
def vehicle_retail(db, company_a, customer_retail):
    return Vehicle.objects.create(
        company=company_a,
        customer=customer_retail,
        plate='ABC1234',
        brand='Fiat',
        model='Uno',
        vehicle_type='hatch'
    )

@pytest.fixture
def vehicle_fleet(db, company_a, customer_fleet):
    return Vehicle.objects.create(
        company=company_a,
        customer=customer_fleet,
        plate='XYZ9876',
        brand='Renault',
        model='Master',
        vehicle_type='van'
    )

@pytest.fixture
def service_wash(db, company_a):
    return ServiceType.objects.create(
        company=company_a,
        name='Lavagem Geral',
        default_price=Decimal('50.00'),
        counts_for_loyalty=True,
        loyalty_points_earned=15
    )

@pytest.fixture
def auth_client(client, owner_user):
    client.force_login(owner_user)
    return client

@pytest.fixture
def api_client():
    return APIClient()
