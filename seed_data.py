import os
import sys
import django

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.saas_core.models import Plan, Company, Subscription
from apps.accounts.models import User
from apps.customers.models import Customer, Vehicle
from apps.services.models import ServiceCategory, ServiceType
from apps.orders.models import ServiceOrder
from apps.orders.services import start_service_order, complete_service_order, deliver_service_order
from apps.finance.models import CashCategory, CashEntry
from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount, LoyaltyEvent
from apps.commissions.models import CommissionRule
from apps.appointments.models import Appointment

def run_seed():
    print("🌱 Iniciando carga de dados de demonstração (Seed Data)...")

    # 1. PLANOS COMERCIAIS
    plan_basic, _ = Plan.objects.get_or_create(
        code='basic',
        defaults={
            'name': 'Básico (Start)',
            'description': 'Ideal para lava-jatos pequenos de 1 operador que precisam de controle de pátio.',
            'monthly_price': Decimal('39.90'),
            'max_users': 1,
            'has_mobile_booking': True,
            'has_loyalty': False,
            'has_monthly_billing': False,
            'has_inspections': False,
            'has_commissions': False,
            'has_push_notifications': False,
            'has_custom_reports': False,
        }
    )

    plan_pro, _ = Plan.objects.get_or_create(
        code='pro',
        defaults={
            'name': 'Profissional (Pro)',
            'description': 'Perfeito para negócios em expansão com faturamento mensal de frotas e programa de fidelidade.',
            'monthly_price': Decimal('79.90'),
            'max_users': 3,
            'has_mobile_booking': True,
            'has_loyalty': True,
            'has_monthly_billing': True,
            'has_inspections': False,
            'has_commissions': False,
            'has_push_notifications': False,
            'has_custom_reports': False,
        }
    )

    plan_premium, _ = Plan.objects.get_or_create(
        code='premium',
        defaults={
            'name': 'Premium (Master)',
            'description': 'Plataforma completa para centros automotivos de alto padrão: fotos antes/depois, comissões e relatórios.',
            'monthly_price': Decimal('139.90'),
            'max_users': 10,
            'has_mobile_booking': True,
            'has_loyalty': True,
            'has_monthly_billing': True,
            'has_inspections': True,
            'has_commissions': True,
            'has_push_notifications': True,
            'has_custom_reports': True,
        }
    )
    print("✅ Planos Comerciais sincronizados.")

    # 2. SUPERADMIN DO SAAS
    admin_user = User.objects.filter(email='admin@saas.com').first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            email='admin@saas.com',
            username='admin',
            first_name='Admin',
            last_name='Geral',
            role='superadmin'
        )
        admin_user.set_password('admin')
        admin_user.save()
    print("✅ Superusuário admin@saas.com (senha: admin) pronto.")

    # 3. EMPRESA 3: Auto Brilho VIP (Premium)
    company_premium, _ = Company.objects.get_or_create(
        slug='auto-brilho-vip',
        defaults={
            'name': 'Auto Brilho VIP Detail',
            'plan': plan_premium,
            'status': 'active',
            'email': 'contato@autobrilho.com',
            'phone': '(11) 99888-7766',
            'address': 'Av. dos Bandeirantes, 1500',
            'city': 'São Paulo',
            'state': 'SP',
            'latitude': Decimal('-23.598765'),
            'longitude': Decimal('-46.687654'),
        }
    )

    dono_premium = User.objects.filter(email='dono@autobrilho.com').first()
    if not dono_premium:
        dono_premium = User.objects.create_user(
            email='dono@autobrilho.com',
            username='dono_premium',
            first_name='Carlos',
            last_name='Menezes',
            role='owner',
            company=company_premium
        )
        dono_premium.set_password('dono')
        dono_premium.save()

    # Operador Premium
    operador_premium = User.objects.filter(email='lavador@autobrilho.com').first()
    if not operador_premium:
        operador_premium = User.objects.create_user(
            email='lavador@autobrilho.com',
            username='lavador1',
            first_name='Rodrigo',
            last_name='Santos',
            role='employee',
            company=company_premium
        )
        operador_premium.set_password('dono')
        operador_premium.save()

    # Categorias e Serviços da Auto Brilho VIP
    cat_estetica, _ = ServiceCategory.objects.get_or_create(
        company=company_premium,
        name='Estética Automotiva',
        defaults={'description': 'Polimento, vitrificação e detalhamento.'}
    )
    cat_lavagem, _ = ServiceCategory.objects.get_or_create(
        company=company_premium,
        name='Lavagens Técnicas',
        defaults={'description': 'Lavagem detalhada com snow foam e proteção.'}
    )

    serv_polimento, _ = ServiceType.objects.get_or_create(
        company=company_premium,
        name='Polimento Técnico Comercial',
        defaults={
            'category': cat_estetica,
            'default_price': Decimal('350.00'),
            'estimated_duration_minutes': 180,
            'counts_for_loyalty': True,
            'loyalty_points_earned': 35
        }
    )

    serv_lavagem_vip, _ = ServiceType.objects.get_or_create(
        company=company_premium,
        name='Lavagem Detalhada VIP',
        defaults={
            'category': cat_lavagem,
            'default_price': Decimal('90.00'),
            'estimated_duration_minutes': 60,
            'counts_for_loyalty': True,
            'loyalty_points_earned': 10
        }
    )

    # Regras de Comissão Premium
    CommissionRule.objects.get_or_create(
        company=company_premium,
        service_type=serv_polimento,
        defaults={'calc_type': 'percentage', 'value': Decimal('20.00')}
    )
    CommissionRule.objects.get_or_create(
        company=company_premium,
        service_type=serv_lavagem_vip,
        defaults={'calc_type': 'fixed', 'value': Decimal('15.00')}
    )

    # Programa de Fidelidade Premium
    LoyaltyProgram.objects.get_or_create(
        company=company_premium,
        defaults={
            'name': 'Clube VIP Auto Brilho',
            'points_needed_for_reward': 100,
            'reward_description': 'Cristalização de Para-brisa Grátis',
            'points_per_service': 10
        }
    )

    # Usuário Cliente Motorista (App Mobile e Portal Web)
    cliente_user = User.objects.filter(email='cliente@autoflow.com').first()
    if not cliente_user:
        cliente_user = User.objects.create_user(
            email='cliente@autoflow.com',
            username='cliente_vip',
            first_name='Roberto',
            last_name='Guimarães',
            role='customer',
            phone='(11) 98765-4321',
            company=company_premium
        )
        cliente_user.set_password('123')
        cliente_user.save()

    # Clientes & Veículos Premium
    cust_vip = Customer.objects.filter(company=company_premium, name='Dr. Roberto Guimarães').first()
    if not cust_vip:
        cust_vip = Customer.objects.create(
            company=company_premium,
            user=cliente_user,
            name='Dr. Roberto Guimarães',
            phone='(11) 98765-4321',
            email='cliente@autoflow.com',
            billing_type='per_service'
        )
    else:
        cust_vip.user = cliente_user
        cust_vip.email = 'cliente@autoflow.com'
        cust_vip.save()

    veh_bmw, _ = Vehicle.objects.get_or_create(
        company=company_premium,
        plate='VIP3B33',
        defaults={
            'customer': cust_vip,
            'brand': 'BMW',
            'model': '320i M Sport',
            'color': 'Azul Portimão',
            'vehicle_type': 'sedan'
        }
    )

    cust_frota, _ = Customer.objects.get_or_create(
        company=company_premium,
        name='Executiva Locadora & Blindados',
        defaults={
            'phone': '(11) 97777-8888',
            'email': 'contato@executivalocadora.com.br',
            'billing_type': 'monthly'
        }
    )

    veh_hilux, _ = Vehicle.objects.get_or_create(
        company=company_premium,
        plate='FRO1T01',
        defaults={
            'customer': cust_frota,
            'brand': 'Toyota',
            'model': 'Hilux SRX',
            'color': 'Prata',
            'vehicle_type': 'pickup'
        }
    )

    # Ordens de demonstração no pátio Premium
    # OS 1: Em execução
    order1, created1 = ServiceOrder.objects.get_or_create(
        company=company_premium,
        vehicle=veh_bmw,
        status='in_progress',
        defaults={
            'customer': cust_vip,
            'service_type': serv_polimento,
            'assigned_to': operador_premium,
            'price': Decimal('350.00'),
            'final_price': Decimal('350.00'),
            'started_at': timezone.now() - timedelta(minutes=45),
            'notes': 'Cliente solicitou proteção extra de cera de carnaúba.'
        }
    )

    # OS 2: Aguardando
    order2, created2 = ServiceOrder.objects.get_or_create(
        company=company_premium,
        vehicle=veh_hilux,
        status='waiting',
        defaults={
            'customer': cust_frota,
            'service_type': serv_lavagem_vip,
            'assigned_to': None,
            'price': Decimal('90.00'),
            'final_price': Decimal('90.00'),
            'notes': 'Frota mensal. Lavagem de chassi solicitada.'
        }
    )

    # 4. EMPRESA 2: Pro Wash Detail (Plano Pro)
    company_pro, _ = Company.objects.get_or_create(
        slug='pro-wash-detail',
        defaults={
            'name': 'Pro Wash Detail',
            'plan': plan_pro,
            'status': 'active',
            'email': 'contato@prowash.com',
            'phone': '(21) 98888-2233',
            'address': 'Rua das Flores, 45',
            'city': 'Rio de Janeiro',
            'state': 'RJ',
        }
    )

    dono_pro = User.objects.filter(email='dono.pro@teste.com').first()
    if not dono_pro:
        dono_pro = User.objects.create_user(
            email='dono.pro@teste.com',
            username='dono_pro',
            first_name='Marcos',
            last_name='Pro',
            role='owner',
            company=company_pro
        )
        dono_pro.set_password('dono')
        dono_pro.save()

    serv_lav_pro, _ = ServiceType.objects.get_or_create(
        company=company_pro,
        name='Lavagem Completa com Cera',
        defaults={'default_price': Decimal('60.00'), 'estimated_duration_minutes': 45}
    )

    # 5. EMPRESA 1: Lava-Jato Central (Plano Básico)
    company_basic, _ = Company.objects.get_or_create(
        slug='lava-jato-central',
        defaults={
            'name': 'Lava-Jato Central',
            'plan': plan_basic,
            'status': 'active',
            'email': 'central@email.com',
            'phone': '(31) 97777-1122',
            'address': 'Av. Principal, 100',
            'city': 'Belo Horizonte',
            'state': 'MG',
        }
    )

    dono_basic = User.objects.filter(email='dono.basico@teste.com').first()
    if not dono_basic:
        dono_basic = User.objects.create_user(
            email='dono.basico@teste.com',
            username='dono_basico',
            first_name='José',
            last_name='Central',
            role='owner',
            company=company_basic
        )
        dono_basic.set_password('dono')
        dono_basic.save()

    serv_ducha, _ = ServiceType.objects.get_or_create(
        company=company_basic,
        name='Ducha Rápida & Aspiração',
        defaults={'default_price': Decimal('40.00'), 'estimated_duration_minutes': 30}
    )

    print("✅ 3 Empresas (Auto Brilho VIP, Pro Wash e Central) provisionadas com sucesso!")
    print("\n🎉 Seed Data finalizado com êxito!")

if __name__ == '__main__':
    run_seed()
