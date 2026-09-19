import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_company_api_exposes_dynamic_plan_features(api_client, company_a, company_b):
    url = reverse('api:companies_list')
    response = api_client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Verifica se a empresa Premium possui as features habilitadas
    comp_a_data = next(c for c in data if c['slug'] == 'lava-jato-a')
    assert comp_a_data['plan_code'] == 'premium'
    assert comp_a_data['features']['has_loyalty'] is True
    assert comp_a_data['features']['has_inspections'] is True

    # Verifica se a empresa Básica possui as features restritas
    comp_b_data = next(c for c in data if c['slug'] == 'lava-jato-b')
    assert comp_b_data['plan_code'] == 'basic'
    assert comp_b_data['features']['has_loyalty'] is False
    assert comp_b_data['features']['has_inspections'] is False


@pytest.mark.django_db
def test_mobile_api_vehicle_delete_and_appointment_cancel(api_client, company_a, service_wash):
    from apps.accounts.models import User
    from apps.customers.models import Customer, Vehicle
    from apps.appointments.models import Appointment
    from rest_framework_simplejwt.tokens import RefreshToken
    from django.utils import timezone

    customer_user = User.objects.create_user(
        email='customer.mobile@teste.com',
        username='customer_mobile',
        role='customer',
    )
    customer_user.set_password('senha123')
    customer_user.save()

    customer = Customer.objects.create(
        company=company_a,
        user=customer_user,
        name="Cliente Mobile",
        phone="11988887777",
        email=customer_user.email,
    )
    vehicle = Vehicle.objects.create(
        company=company_a,
        customer=customer,
        plate="MOB1234",
        brand="VW",
        model="Gol",
        vehicle_type="hatch",
    )

    token = str(RefreshToken.for_user(customer_user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # Test Cancel Appointment
    appointment = Appointment.objects.create(
        company=company_a,
        customer=customer,
        vehicle=vehicle,
        service_type=service_wash,
        scheduled_date=timezone.now().date() + timezone.timedelta(days=1),
        scheduled_time=timezone.now().time(),
        status='pending',
    )
    cancel_url = reverse('api:cancel_appointment', kwargs={'pk': appointment.pk})
    resp_cancel = api_client.post(cancel_url)
    assert resp_cancel.status_code == 200
    appointment.refresh_from_db()
    assert appointment.status == 'cancelled'

    # Test Delete Vehicle
    del_url = reverse('api:customer_vehicle_detail', kwargs={'pk': vehicle.pk})
    resp_del = api_client.delete(del_url)
    assert resp_del.status_code == 204


@pytest.mark.django_db
def test_mobile_api_all_loyalty_accounts(api_client, company_a, company_b):
    from apps.accounts.models import User
    from apps.customers.models import Customer
    from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount
    from rest_framework_simplejwt.tokens import RefreshToken

    customer_user = User.objects.create_user(
        email='multi.loyalty@teste.com',
        username='multi_loyalty',
        role='customer',
    )
    customer_user.set_password('senha123')
    customer_user.save()

    cust_a = Customer.objects.create(
        company=company_a,
        user=customer_user,
        name="Customer Multi",
        phone="11999999999",
        email=customer_user.email,
    )
    cust_b = Customer.objects.create(
        company=company_b,
        user=customer_user,
        name="Customer Multi",
        phone="11999999999",
        email=customer_user.email,
    )
    LoyaltyProgram.objects.create(company=company_a, name="VIP A", points_needed_for_reward=100)
    LoyaltyProgram.objects.create(company=company_b, name="VIP B", points_needed_for_reward=50)

    LoyaltyAccount.objects.create(company=company_a, customer=cust_a, points_balance=80)
    LoyaltyAccount.objects.create(company=company_b, customer=cust_b, points_balance=35)

    token = str(RefreshToken.for_user(customer_user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    url = reverse('api:customer_all_loyalty')
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    slugs = [d['company_slug'] for d in data]
    assert 'lava-jato-a' in slugs
    assert 'lava-jato-b' in slugs

