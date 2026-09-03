import pytest
from datetime import date, time
from decimal import Decimal
from django.urls import reverse
from apps.accounts.models import User
from apps.saas_core.models import Plan, Company
from apps.customers.models import Customer, Vehicle
from apps.services.models import ServiceCategory, ServiceType
from apps.appointments.models import Appointment

@pytest.fixture
def portal_setup(db):
    plan = Plan.objects.create(
        code='premium',
        name='Master VIP',
        monthly_price=Decimal('139.90'),
        has_mobile_booking=True,
        has_loyalty=True,
        has_inspections=True
    )
    company = Company.objects.create(
        name='Lava-Jato Premium',
        slug='lava-jato-premium',
        plan=plan,
        status='active'
    )
    customer_user = User.objects.create_user(
        email='motorista@teste.com',
        username='motorista',
        first_name='Carlos',
        last_name='Silva',
        role='customer',
        password='pass123customer'
    )
    customer = Customer.objects.create(
        company=company,
        user=customer_user,
        name='Carlos Silva',
        phone='11988887777',
        email='motorista@teste.com'
    )
    vehicle = Vehicle.objects.create(
        company=company,
        customer=customer,
        plate='BRA2E19',
        brand='Honda',
        model='Civic',
        color='Preto'
    )
    category = ServiceCategory.objects.create(
        company=company,
        name='Lavagens Especiais'
    )
    service = ServiceType.objects.create(
        company=company,
        category=category,
        name='Lavagem Detalhada + Cera',
        default_price=Decimal('120.00'),
        estimated_duration_minutes=60,
        loyalty_points_earned=25,
        is_active=True
    )
    return {
        'company': company,
        'customer_user': customer_user,
        'customer': customer,
        'vehicle': vehicle,
        'service': service,
    }


@pytest.mark.django_db
def test_guest_can_view_portal(client, portal_setup):
    url = reverse('portal:home')
    response = client.get(url)
    assert response.status_code == 200
    assert 'Lava-Jato Premium' in response.content.decode('utf-8')
    assert 'Lavagem Detalhada + Cera' in response.content.decode('utf-8')


@pytest.mark.django_db
def test_customer_login_redirects_to_portal_select_company(client, portal_setup):
    login_url = reverse('accounts:login')
    response = client.post(login_url, {
        'username': 'motorista@teste.com',
        'password': 'pass123customer'
    })
    assert response.status_code == 302
    assert response.url == reverse('portal:select_company')


@pytest.mark.django_db
def test_select_company_view_with_recent_order(client, portal_setup):
    from apps.orders.models import ServiceOrder
    data = portal_setup
    client.force_login(data['customer_user'])

    # Cria ordem de serviço prévia para aparecer como último lava-jato
    ServiceOrder.objects.create(
        company=data['company'],
        customer=data['customer'],
        vehicle=data['vehicle'],
        service_type=data['service'],
        status='completed',
        price=Decimal('120.00')
    )

    url = reverse('portal:select_company')
    response = client.get(url)
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert 'Último Lava-Jato que você foi' in content
    assert 'Lava-Jato Premium' in content
    assert 'Desejo ir neste novamente' in content


@pytest.mark.django_db
def test_select_company_search_filter(client, portal_setup):
    url = reverse('portal:select_company')
    response = client.get(url + '?q=Premium')
    assert response.status_code == 200
    assert 'Lava-Jato Premium' in response.content.decode('utf-8')

    response_empty = client.get(url + '?q=Inexistente123XYZ')
    assert response_empty.status_code == 200
    assert 'Nenhum lava-jato encontrado' in response_empty.content.decode('utf-8')


@pytest.mark.django_db
def test_customer_can_book_appointment(client, portal_setup):
    data = portal_setup
    client.force_login(data['customer_user'])

    book_url = reverse('portal:book_appointment')
    response = client.post(book_url, {
        'company_id': data['company'].id,
        'service_type_id': data['service'].id,
        'vehicle_id': data['vehicle'].id,
        'scheduled_date': '2026-10-15',
        'scheduled_time': '14:00',
        'notes': 'Favor dar atenção especial nas rodas'
    })

    assert response.status_code == 302
    appt = Appointment.objects.filter(
        company=data['company'],
        customer=data['customer'],
        vehicle=data['vehicle'],
        service_type=data['service']
    ).first()

    assert appt is not None
    assert appt.scheduled_date == date(2026, 10, 15)
    assert appt.scheduled_time == time(14, 0)
    assert appt.status == 'pending'
    assert 'rodas' in appt.notes


@pytest.mark.django_db
def test_customer_can_add_vehicle_to_garage(client, portal_setup):
    data = portal_setup
    client.force_login(data['customer_user'])

    add_vehicle_url = reverse('portal:add_vehicle')
    response = client.post(add_vehicle_url, {
        'plate': 'vip9999',
        'brand': 'Porsche',
        'model': '911 Carrera',
        'color': 'Amarelo',
        'vehicle_type': 'sedan'
    })

    assert response.status_code == 302
    v = Vehicle.objects.filter(plate='VIP9999').first()
    assert v is not None
    assert v.brand == 'Porsche'
    assert v.model == '911 Carrera'
    assert v.customer == data['customer']


@pytest.mark.django_db
def test_customer_can_cancel_pending_appointment(client, portal_setup):
    data = portal_setup
    client.force_login(data['customer_user'])

    appt = Appointment.objects.create(
        company=data['company'],
        customer=data['customer'],
        vehicle=data['vehicle'],
        service_type=data['service'],
        scheduled_date=date(2026, 10, 20),
        scheduled_time=time(10, 0),
        status='pending'
    )

    cancel_url = reverse('portal:cancel_appointment', kwargs={'appointment_id': appt.id})
    response = client.get(cancel_url)
    assert response.status_code == 302

    appt.refresh_from_db()
    assert appt.status == 'cancelled'


@pytest.mark.django_db
def test_authenticated_customer_with_loyalty_can_view_portal(client, portal_setup):
    from apps.loyalty.models import LoyaltyAccount, LoyaltyEvent
    data = portal_setup
    client.force_login(data['customer_user'])

    account = LoyaltyAccount.objects.create(
        company=data['company'],
        customer=data['customer'],
        points_balance=40,
        total_points_earned=40
    )
    LoyaltyEvent.objects.create(
        company=data['company'],
        account=account,
        event_type='earned',
        points=40,
        description='Lavagem VIP'
    )

    url = reverse('portal:home')
    response = client.get(url)
    assert response.status_code == 200
    assert '40' in response.content.decode('utf-8')


@pytest.mark.django_db
def test_authenticated_customer_with_active_order_and_photos(client, portal_setup):
    from apps.orders.models import ServiceOrder, OrderPhoto
    data = portal_setup
    client.force_login(data['customer_user'])

    order = ServiceOrder.objects.create(
        company=data['company'],
        customer=data['customer'],
        vehicle=data['vehicle'],
        service_type=data['service'],
        status='in_progress',
        price=Decimal('120.00')
    )

    url = reverse('portal:home')
    response = client.get(url)
    assert response.status_code == 200
    assert data['vehicle'].plate in response.content.decode('utf-8')


