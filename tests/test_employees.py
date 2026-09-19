import pytest
from decimal import Decimal
from datetime import date
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.saas_core.models import Company, Plan
from apps.employees.models import RegisteredEmployee, SalaryPayment, DailyHelper, DailyWork
from apps.employees.services import record_salary_payment, pay_daily_work
from apps.finance.models import CashEntry

@pytest.fixture
def premium_company(db):
    plan_premium, _ = Plan.objects.get_or_create(
        code='premium',
        defaults={
            'name': 'Plano Master / Premium',
            'monthly_price': Decimal('299.90'),
            'max_users': 50,
            'has_commissions': True,
        }
    )
    company = Company.objects.create(
        name='Estética Automotiva Premium Master',
        slug='estetica-automotiva-premium-master',
        document='11.222.333/0001-44',
        phone='(11) 99999-0000',
        plan=plan_premium,
        status='active'
    )
    return company


@pytest.fixture
def basic_company(db):
    plan_basic, _ = Plan.objects.get_or_create(
        code='start',
        defaults={
            'name': 'Plano Start / Básico',
            'monthly_price': Decimal('89.90'),
            'max_users': 5,
            'has_commissions': False,
        }
    )
    company = Company.objects.create(
        name='Lava-Jato Simples',
        slug='lava-jato-simples',
        document='22.333.444/0001-55',
        phone='(11) 98888-0000',
        plan=plan_basic,
        status='active'
    )
    return company


@pytest.fixture
def premium_owner(db, premium_company):
    return User.objects.create_user(
        email='dono_prem@autobrilho.com',
        username='dono_prem',
        password='password123',
        role='owner',
        company=premium_company
    )


@pytest.fixture
def basic_owner(db, basic_company):
    return User.objects.create_user(
        email='dono_bas@autobrilho.com',
        username='dono_bas',
        password='password123',
        role='owner',
        company=basic_company
    )


@pytest.mark.django_db
def test_premium_plan_can_access_employees_and_basic_is_blocked(client, premium_owner, basic_owner):
    # Dono com plano Premium tem acesso
    client.force_login(premium_owner)
    res_prem = client.get(reverse('employees:dashboard'), HTTP_HOST='localhost')
    assert res_prem.status_code == 200
    assert 'Controle de Equipe e Diaristas' in res_prem.content.decode('utf-8')
    assert 'Funcionários' in res_prem.content.decode('utf-8')

    # Dono com plano Básico é redirecionado/bloqueado
    client.force_login(basic_owner)
    res_bas = client.get(reverse('employees:dashboard'), HTTP_HOST='localhost')
    assert res_bas.status_code == 302


@pytest.mark.django_db
def test_registered_employee_lifecycle_and_cash_deduction(client, premium_company, premium_owner):
    client.force_login(premium_owner)

    # 1. Cadastro de Funcionário Registrado
    payload = {
        'name': 'Marcos Vinícius Silva',
        'role_title': 'Detalhador Automotivo Chefe',
        'cpf': '123.456.789-00',
        'phone': '(11) 98765-4321',
        'monthly_salary': '2800.00',
        'payment_day': 5,
        'hire_date': '2026-01-10',
        'pix_key': '12345678900',
        'is_active': True,
        'notes': 'Especialista em vitrificação 9H',
    }
    res = client.post(reverse('employees:registered_employee_create'), payload, HTTP_HOST='localhost')
    assert res.status_code == 302
    assert res.url == '/employees/?tab=registered'

    emp = RegisteredEmployee.objects.get(company=premium_company, name='Marcos Vinícius Silva')
    assert emp.monthly_salary == Decimal('2800.00')
    assert emp.role_title == 'Detalhador Automotivo Chefe'

    # 2. Pagamento de Salário com Desconto e Bônus
    payment = record_salary_payment(
        employee=emp,
        reference_month='03/2026',
        base_salary=emp.monthly_salary,
        bonus=Decimal('200.00'),
        deductions=Decimal('100.00'),
        payment_date=date(2026, 3, 5),
        payment_method='pix'
    )
    assert payment.total_paid == Decimal('2900.00') # 2800 + 200 - 100

    # 3. Verifica que a saída foi lançada no Livro Caixa / PDV
    cash_entry = CashEntry.objects.filter(company=premium_company, entry_type='expense', amount=Decimal('2900.00')).first()
    assert cash_entry is not None
    assert 'Pagamento de Salário - Marcos Vinícius Silva' in cash_entry.description
    assert cash_entry.category.name == 'Salários e Diárias'


@pytest.mark.django_db
def test_daily_helper_and_work_lifecycle_and_cash_deduction(client, premium_company, premium_owner):
    client.force_login(premium_owner)

    # 1. Cadastra Ajudante Diário
    helper = DailyHelper.objects.create(
        company=premium_company,
        name='Lucas Diarista',
        phone='(11) 97777-8888',
        pix_key='lucas@pix.com'
    )

    # 2. Registra Diária de Trabalho como Pendente
    work = DailyWork.objects.create(
        company=premium_company,
        helper=helper,
        work_date=date(2026, 3, 4),
        shift='full_day',
        daily_rate=Decimal('130.00'),
        activity_description='Secagem e acabamento interno',
        status='pending',
        payment_method='pix'
    )
    assert work.status == 'pending'
    assert work.cash_entry is None

    # 3. Executa a baixa / pagamento da diária
    pay_daily_work(work)
    work.refresh_from_db()
    assert work.status == 'paid'
    assert work.paid_at is not None
    assert work.cash_entry is not None
    assert work.cash_entry.amount == Decimal('130.00')
    assert work.cash_entry.entry_type == 'expense'
    assert 'Pagamento Diária - Lucas Diarista' in work.cash_entry.description


@pytest.mark.django_db
def test_salary_notification_until_5th_business_day(client, premium_company, premium_owner):
    client.force_login(premium_owner)

    # Cadastra funcionário registrado sem pagamento efetuado no mês
    RegisteredEmployee.objects.create(
        company=premium_company,
        name='Carlos Eduardo',
        role_title='Polidor',
        monthly_salary=Decimal('2500.00'),
        is_active=True
    )

    # Carrega página principal e valida contexto de notificação
    response = client.get('/', HTTP_HOST='localhost')
    assert response.status_code == 200
    notifs = response.context['notifications']
    salary_notifs = [n for n in notifs if n['type'] in ['salary_due', 'salary_late']]
    assert len(salary_notifs) >= 1
    assert '5º dia útil' in salary_notifs[0]['message']
    assert 'Carlos Eduardo' not in salary_notifs[0]['message'] # resumo quantitativo
    assert 'colaborador(es) aguardando pagamento' in salary_notifs[0]['message']


@pytest.mark.django_db
def test_employee_active_inactive_toggle_and_notification_exclusion(client, premium_company, premium_owner):
    client.force_login(premium_owner)

    # 1. Cria funcionário ativo
    emp = RegisteredEmployee.objects.create(
        company=premium_company,
        name='Roberto Silva',
        role_title='Lavador Geral',
        monthly_salary=Decimal('2200.00'),
        is_active=True
    )

    # Verifica que com funcionário ativo e sem pagamento, o alerta de salário é gerado
    res1 = client.get('/', HTTP_HOST='localhost')
    assert res1.status_code == 200
    salary_notifs = [n for n in res1.context['notifications'] if n['type'] in ['salary_due', 'salary_late']]
    assert len(salary_notifs) == 1

    # 2. Desativa o funcionário (demissão / desligamento) através da rota toggle_status
    toggle_res = client.get(reverse('employees:registered_employee_toggle_status', args=[emp.id]), HTTP_HOST='localhost')
    assert toggle_res.status_code == 302
    emp.refresh_from_db()
    assert emp.is_active is False

    # 3. Com o funcionário inativo, o alerta de salário NÃO deve mais ser gerado
    res2 = client.get('/', HTTP_HOST='localhost')
    assert res2.status_code == 200
    salary_notifs_after = [n for n in res2.context['notifications'] if n['type'] in ['salary_due', 'salary_late']]
    assert len(salary_notifs_after) == 0

    # 4. Verifica que no dashboard o funcionário aparece como inativo
    dash_res = client.get(reverse('employees:dashboard') + '?tab=registered', HTTP_HOST='localhost')
    assert dash_res.status_code == 200
    content = dash_res.content.decode('utf-8')
    assert 'Inativo' in content
    assert 'Reativar' in content

    # 5. Reativa o funcionário e valida que volta a ficar ativo
    client.get(reverse('employees:registered_employee_toggle_status', args=[emp.id]), HTTP_HOST='localhost')
    emp.refresh_from_db()
    assert emp.is_active is True

