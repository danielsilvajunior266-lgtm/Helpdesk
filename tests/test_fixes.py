import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.saas_core.models import Company, Plan
from apps.customers.models import Customer, Vehicle
from apps.services.models import ServiceCategory, ServiceType
from apps.orders.models import ServiceOrder
from apps.orders.services import complete_service_order
from apps.finance.models import CashEntry
from apps.loyalty.models import LoyaltyEvent, LoyaltyProgram, LoyaltyAccount
from apps.api.serializers import LoyaltyAccountSerializer, AppointmentSerializer

@pytest.mark.django_db
def test_superuser_can_access_dashboard_without_redirect_loop(client, company_a):
    admin = User.objects.create_superuser(
        email='admin_test@saas.com',
        username='admin_test',
        password='password123',
        role='superadmin'
    )
    client.force_login(admin)
    response = client.get('/', HTTP_HOST='localhost')
    assert response.status_code == 200
    assert response.context['current_company'] is not None


@pytest.mark.django_db
def test_customer_can_create_vehicle_via_api(api_client, company_a):
    customer_user = User.objects.create_user(
        email='driver@gmail.com',
        password='password123',
        role='customer'
    )
    api_client.force_authenticate(user=customer_user)

    url = reverse('api:customer_vehicles')
    data = {
        'plate': 'BRA2E19',
        'brand': 'Volkswagen',
        'model': 'Polo',
        'color': 'Cinza',
        'vehicle_type': 'hatch',
        'company': company_a.id
    }
    response = api_client.post(url, data)
    assert response.status_code == 201
    assert Vehicle.objects.filter(plate='BRA2E19', company=company_a).exists()


@pytest.mark.django_db
def test_username_collision_prevention_on_create_user():
    u1 = User.objects.create_user(email='carlos@empresa1.com', password='pass')
    u2 = User.objects.create_user(email='carlos@empresa2.com', password='pass')
    assert u1.username != u2.username
    assert u1.username == 'carlos'
    assert u2.username == 'carlos_1'


@pytest.mark.django_db
def test_complete_service_order_is_idempotent(company_a, customer_retail, vehicle_retail, service_wash):
    order = ServiceOrder.objects.create(
        company=company_a,
        customer=customer_retail,
        vehicle=vehicle_retail,
        service_type=service_wash,
        price=Decimal('350.00'),
        final_price=Decimal('350.00'),
        status='in_progress'
    )

    # Primeira conclusão
    complete_service_order(order, payment_method='pix')
    cash_count_1 = CashEntry.objects.filter(company=company_a, order=order).count()
    loyalty_count_1 = LoyaltyEvent.objects.filter(company=company_a, order=order, event_type='earned').count()
    assert cash_count_1 == 1
    assert loyalty_count_1 == 1

    # Segunda conclusão (simulando duplo clique)
    complete_service_order(order, payment_method='pix')
    cash_count_2 = CashEntry.objects.filter(company=company_a, order=order).count()
    loyalty_count_2 = LoyaltyEvent.objects.filter(company=company_a, order=order, event_type='earned').count()
    assert cash_count_2 == 1
    assert loyalty_count_2 == 1


@pytest.mark.django_db
def test_loyalty_account_serializer_resolves_program_attributes(company_a, customer_retail):
    program = LoyaltyProgram.objects.create(
        company=company_a,
        name='Programa VIP',
        points_needed_for_reward=80,
        reward_description='Lavagem de Motor Grátis'
    )
    account = LoyaltyAccount.objects.create(
        company=company_a,
        customer=customer_retail,
        points_balance=50
    )

    serializer = LoyaltyAccountSerializer(account)
    data = serializer.data
    assert data['reward_description'] == 'Lavagem de Motor Grátis'
    assert data['points_needed'] == 80


@pytest.mark.django_db
def test_appointment_serializer_validates_cross_tenant_and_vehicle(company_a, company_b, customer_retail, vehicle_retail, service_wash):
    # Serviço pertencente a company_a mas agendando com company_b
    other_user = User.objects.create_user(email='intruder@saas.com', role='customer')
    
    # Validação 1: Veículo não pertence ao usuário
    serializer = AppointmentSerializer(
        data={
            'company': company_a.id,
            'vehicle': vehicle_retail.id,
            'service_type': service_wash.id,
            'scheduled_date': '2026-09-10',
            'scheduled_time': '10:00',
        },
        context={'request': type('Req', (), {'user': other_user, 'is_authenticated': True})()}
    )
    assert not serializer.is_valid()
    assert 'vehicle' in serializer.errors

    # Validação 2: Serviço não pertence à empresa
    user_owner = customer_retail.user or User.objects.create_user(email='veh_owner@saas.com', role='customer')
    customer_retail.user = user_owner
    customer_retail.save()

    serializer2 = AppointmentSerializer(
        data={
            'company': company_b.id,
            'vehicle': vehicle_retail.id,
            'service_type': service_wash.id,
            'scheduled_date': '2026-09-10',
            'scheduled_time': '10:00',
        },
        context={'request': type('Req', (), {'user': user_owner, 'is_authenticated': True})()}
    )
    assert not serializer2.is_valid()
    assert 'service_type' in serializer2.errors


@pytest.mark.django_db
def test_customer_vip_status_3_consecutive_months_and_inactivity_expiration(company_a, customer_retail, vehicle_retail, service_wash):
    from datetime import datetime
    from django.utils import timezone

    # 1. Sem ordens ou apenas 2 meses -> is_vip False
    assert not customer_retail.is_vip

    # Mês 1: Julho 2026
    o1 = ServiceOrder.objects.create(
        company=company_a,
        customer=customer_retail,
        vehicle=vehicle_retail,
        service_type=service_wash,
        price=Decimal('50.00'),
        final_price=Decimal('50.00'),
        status='completed'
    )
    o1.created_at = timezone.make_aware(datetime(2026, 7, 10, 10, 0))
    o1.save()

    # Mês 2: Agosto 2026
    o2 = ServiceOrder.objects.create(
        company=company_a,
        customer=customer_retail,
        vehicle=vehicle_retail,
        service_type=service_wash,
        price=Decimal('50.00'),
        final_price=Decimal('50.00'),
        status='completed'
    )
    o2.created_at = timezone.make_aware(datetime(2026, 8, 15, 10, 0))
    o2.save()

    assert not customer_retail.is_vip  # Apenas 2 meses consecutivos

    # Mês 3: Setembro 2026
    o3 = ServiceOrder.objects.create(
        company=company_a,
        customer=customer_retail,
        vehicle=vehicle_retail,
        service_type=service_wash,
        price=Decimal('50.00'),
        final_price=Decimal('50.00'),
        status='completed'
    )
    o3.created_at = timezone.make_aware(datetime(2026, 9, 3, 10, 0))
    o3.save()

    # Agora o cliente completou 3 meses consecutivos: Jul, Ago, Set -> É VIP!
    assert customer_retail.is_vip is True

    # Se a última visita tiver ocorrido há 2 meses ou mais (ex: última em Junho 2026) -> Perde o VIP
    o1.created_at = timezone.make_aware(datetime(2026, 4, 1, 10, 0))
    o1.save()
    o2.created_at = timezone.make_aware(datetime(2026, 5, 1, 10, 0))
    o2.save()
    o3.created_at = timezone.make_aware(datetime(2026, 6, 1, 10, 0))
    o3.save()
    # Teve Abr, Mai, Jun (3 meses consecutivos), mas hoje em Setembro (> 2 meses sem visitar) -> Perdeu o VIP!
    assert not customer_retail.is_vip


@pytest.mark.django_db
def test_operational_notifications_in_tenant_context(client, company_a, customer_retail, vehicle_retail, service_wash):
    from apps.appointments.models import Appointment
    from datetime import date, time

    owner = User.objects.create_user(
        email='owner_test@saas.com',
        username='owner_test',
        password='password123',
        role='tenant_admin',
        company=company_a
    )
    client.force_login(owner)

    # Cria um agendamento pendente
    Appointment.objects.create(
        company=company_a,
        customer=customer_retail,
        vehicle=vehicle_retail,
        service_type=service_wash,
        scheduled_date=date.today(),
        scheduled_time=time(14, 30),
        status='pending'
    )

    response = client.get('/', HTTP_HOST='localhost')
    assert response.status_code == 200
    assert 'notifications' in response.context
    notifs = response.context['notifications']
    assert any(n['type'] == 'appointment' for n in notifs)
    assert any(n['type'] in ['license_ok', 'plan_active'] for n in notifs)
    assert response.context['unread_notifications_count'] >= 1
    # Verifica que "Portal do Motorista" não está mais no sidebar
    assert 'Portal do Motorista' not in response.content.decode('utf-8')


@pytest.mark.django_db
def test_customer_registration_web_view_and_role_restriction(client):
    # 1. Carrega tela de cadastro
    res_get = client.get(reverse('accounts:register'), HTTP_HOST='localhost')
    assert res_get.status_code == 200
    assert 'Criar Conta de Cliente' in res_get.content.decode('utf-8')

    # 2. Cadastro válido
    payload = {
        'full_name': 'Carlos Silva Santos',
        'email': 'carlos.silva@exemplo.com',
        'phone': '(11) 98765-4321',
        'password': 'password123',
        'confirm_password': 'password123',
    }
    res_post = client.post(reverse('accounts:register'), payload, HTTP_HOST='localhost')
    assert res_post.status_code == 302
    assert res_post.url == reverse('portal:select_company')

    # 3. Verifica que o usuário foi criado estritamente como 'customer'
    created_user = User.objects.get(email='carlos.silva@exemplo.com')
    assert created_user.role == 'customer'
    assert created_user.first_name == 'Carlos'
    assert created_user.last_name == 'Silva Santos'
    assert created_user.company is None
    assert created_user.is_staff is False
    assert created_user.is_superuser is False


@pytest.mark.django_db
def test_loyalty_service_reward_configuration_and_100_points_notification(auth_client, company_a, customer_retail, service_wash):
    from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount

    # 1. Configura o programa escolhendo o serviço recompensa do lava jato
    res_cfg = auth_client.post(reverse('loyalty:configure'), {
        'reward_type': 'service',
        'reward_service_id': service_wash.id,
        'points_needed_for_reward': 100,
        'is_active': 'on'
    })
    assert res_cfg.status_code == 302

    program = LoyaltyProgram.objects.get(company=company_a)
    assert program.reward_service == service_wash
    assert program.reward_name == service_wash.name
    assert program.points_needed_for_reward == 100

    # 2. Cliente atinge 100 pontos
    account, _ = LoyaltyAccount.objects.get_or_create(
        company=company_a,
        customer=customer_retail,
        defaults={'points_balance': 0, 'total_points_earned': 0}
    )
    account.points_balance = 100
    account.total_points_earned = 100
    account.save()

    # 3. Verifica que a notificação de 100 pontos premiados foi disparada para o dono
    res_page = auth_client.get('/')
    assert res_page.status_code == 200
    notifs = res_page.context['notifications']
    loyalty_notifs = [n for n in notifs if n['type'] == 'loyalty_reward_available']
    assert len(loyalty_notifs) == 1
    assert customer_retail.name in loyalty_notifs[0]['title']
    assert service_wash.name in loyalty_notifs[0]['message']
    assert '100 pontos' in loyalty_notifs[0]['message']

    # 4. Resgate do prêmio
    res_redeem = auth_client.get(reverse('loyalty:redeem', kwargs={'account_id': account.id}))
    assert res_redeem.status_code == 302
    account.refresh_from_db()
    assert account.points_balance == 0
    assert account.total_rewards_redeemed == 1

    # 5. Configura com produto / brinde físico
    res_cfg_prod = auth_client.post(reverse('loyalty:configure'), {
        'reward_type': 'product',
        'reward_product_name': "Cera Meguiar's Premium",
        'points_needed_for_reward': 150,
        'is_active': 'on'
    })
    assert res_cfg_prod.status_code == 302
    program.refresh_from_db()
    assert program.reward_product_name == "Cera Meguiar's Premium"
    assert program.reward_name == "Cera Meguiar's Premium"
    assert program.points_needed_for_reward == 150


@pytest.mark.django_db
def test_create_service_with_custom_loyalty_points(auth_client, company_a):
    from apps.services.models import ServiceType

    payload = {
        'name': 'Polimento Técnico Premium',
        'default_price': '180.00',
        'estimated_duration_minutes': '120',
        'description': 'Polimento e vitrificação de pintura',
        'counts_for_loyalty': 'on',
        'loyalty_points_earned': '35',
    }

    res = auth_client.post(reverse('services:create'), payload)
    assert res.status_code == 302

    created_service = ServiceType.objects.get(company=company_a, name='Polimento Técnico Premium')
    assert created_service.counts_for_loyalty is True
    assert created_service.loyalty_points_earned == 35





