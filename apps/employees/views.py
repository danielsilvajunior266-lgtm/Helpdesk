from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from apps.saas_core.decorators import tenant_required, require_plan_feature
from apps.employees.models import RegisteredEmployee, SalaryPayment, DailyHelper, DailyWork
from apps.employees.forms import RegisteredEmployeeForm, SalaryPaymentForm, DailyHelperForm, DailyWorkForm
from apps.employees.services import record_salary_payment, pay_daily_work

def get_previous_ref_month(today=None):
    if today is None:
        today = timezone.now().date()
    if today.month == 1:
        return f"12/{today.year - 1}"
    return f"{today.month - 1:02d}/{today.year}"


@tenant_required
@require_plan_feature('employees')
def employee_dashboard(request):
    company = request.company
    today = timezone.now().date()
    current_ref_month = get_previous_ref_month(today)

    # Querysets
    registered_employees = RegisteredEmployee.objects.filter(company=company).order_by('-is_active', 'name')
    daily_helpers = DailyHelper.objects.filter(company=company)
    daily_works = DailyWork.objects.filter(company=company).select_related('helper', 'cash_entry')
    salary_payments = SalaryPayment.objects.filter(company=company).select_related('employee', 'cash_entry')

    # Métricas
    total_active_employees = registered_employees.filter(is_active=True).count()
    total_inactive_employees = registered_employees.filter(is_active=False).count()
    total_monthly_payroll = registered_employees.filter(is_active=True).aggregate(Sum('monthly_salary'))['monthly_salary__sum'] or Decimal('0.00')
    total_daily_helpers = daily_helpers.count()

    current_month_daily_paid = daily_works.filter(
        work_date__year=today.year,
        work_date__month=today.month,
        status='paid'
    ).aggregate(Sum('daily_rate'))['daily_rate__sum'] or Decimal('0.00')

    current_month_salary_paid = salary_payments.filter(
        payment_date__year=today.year,
        payment_date__month=today.month,
        status='paid'
    ).aggregate(Sum('total_paid'))['total_paid__sum'] or Decimal('0.00')

    total_staff_invested_month = current_month_daily_paid + current_month_salary_paid

    # Diárias pendentes
    pending_daily_count = daily_works.filter(status='pending').count()
    pending_daily_amount = daily_works.filter(status='pending').aggregate(Sum('daily_rate'))['daily_rate__sum'] or Decimal('0.00')

    # Mapa de status de pagamento dos funcionários no mês de referência (mês anterior)
    paid_employee_ids_this_month = set(salary_payments.filter(
        reference_month=current_ref_month,
        status='paid'
    ).values_list('employee_id', flat=True))

    employees_data = []
    for emp in registered_employees:
        is_paid = emp.id in paid_employee_ids_this_month
        employees_data.append({
            'employee': emp,
            'is_paid_this_month': is_paid,
        })

    active_tab = request.GET.get('tab', 'helpers')

    return render(request, 'employees/dashboard.html', {
        'active_tab': active_tab,
        'current_ref_month': current_ref_month,
        'registered_employees': employees_data,
        'daily_helpers': daily_helpers,
        'daily_works': daily_works[:50],
        'salary_payments': salary_payments[:50],
        'total_active_employees': total_active_employees,
        'total_inactive_employees': total_inactive_employees,
        'total_monthly_payroll': total_monthly_payroll,
        'total_daily_helpers': total_daily_helpers,
        'current_month_daily_paid': current_month_daily_paid,
        'current_month_salary_paid': current_month_salary_paid,
        'total_staff_invested_month': total_staff_invested_month,
        'pending_daily_count': pending_daily_count,
        'pending_daily_amount': pending_daily_amount,
    })


# ==============================================================================
# 1. AJUDANTES DIÁRIOS (DIARISTAS) & DIÁRIAS
# ==============================================================================

@tenant_required
@require_plan_feature('employees')
def daily_helper_create(request):
    if request.method == 'POST':
        form = DailyHelperForm(request.POST)
        if form.is_valid():
            helper = form.save(commit=False)
            helper.company = request.company
            helper.save()
            messages.success(request, f"Ajudante Diário '{helper.name}' cadastrado com sucesso!")
            return redirect('/employees/?tab=helpers')
    else:
        form = DailyHelperForm()

    return render(request, 'employees/daily_helper_form.html', {
        'form': form,
        'title': 'Cadastrar Novo Ajudante Diário',
        'is_edit': False
    })


@tenant_required
@require_plan_feature('employees')
def daily_helper_edit(request, helper_id):
    helper = get_object_or_404(DailyHelper, id=helper_id, company=request.company)
    if request.method == 'POST':
        form = DailyHelperForm(request.POST, instance=helper)
        if form.is_valid():
            form.save()
            messages.success(request, f"Dados do ajudante '{helper.name}' atualizados com sucesso!")
            return redirect('/employees/?tab=helpers')
    else:
        form = DailyHelperForm(instance=helper)

    return render(request, 'employees/daily_helper_form.html', {
        'form': form,
        'title': f"Editar Ajudante: {helper.name}",
        'is_edit': True,
        'helper': helper
    })


@tenant_required
@require_plan_feature('employees')
def daily_work_create(request):
    company = request.company
    if not DailyHelper.objects.filter(company=company).exists():
        messages.warning(request, "Você precisa cadastrar pelo menos um Ajudante Diário antes de registrar uma diária de trabalho.")
        return redirect('employees:daily_helper_create')

    if request.method == 'POST':
        form = DailyWorkForm(request.POST, company=company)
        if form.is_valid():
            work = form.save(commit=False)
            work.company = company
            mark_as_paid = form.cleaned_data.get('mark_as_paid', False)

            if mark_as_paid:
                work.status = 'paid'
                work.paid_at = timezone.now()
                work.save()
                pay_daily_work(work, payment_method=work.payment_method)
                messages.success(request, f"Diária de R$ {work.daily_rate} para {work.helper.name} registrada e debitada do Livro Caixa com sucesso!")
            else:
                work.status = 'pending'
                work.save()
                messages.success(request, f"Diária de R$ {work.daily_rate} para {work.helper.name} registrada com status Pendente.")

            return redirect('/employees/?tab=helpers')
    else:
        form = DailyWorkForm(company=company)

    return render(request, 'employees/daily_work_form.html', {
        'form': form,
        'title': 'Lançar Nova Diária de Trabalho'
    })


@tenant_required
@require_plan_feature('employees')
def daily_work_pay(request, work_id):
    work = get_object_or_404(DailyWork, id=work_id, company=request.company)
    if work.status == 'paid':
        messages.info(request, "Esta diária já foi marcada como paga.")
    else:
        pay_daily_work(work)
        messages.success(request, f"Diária de R$ {work.daily_rate} paga para {work.helper.name}! Valor lançado como despesa no Livro Caixa.")
    return redirect('/employees/?tab=helpers')


# ==============================================================================
# 2. FUNCIONÁRIOS REGISTRADOS (CONTRATADOS FIXOS) & SALÁRIOS
# ==============================================================================

@tenant_required
@require_plan_feature('employees')
def registered_employee_create(request):
    if request.method == 'POST':
        form = RegisteredEmployeeForm(request.POST)
        if form.is_valid():
            emp = form.save(commit=False)
            emp.company = request.company
            emp.save()
            messages.success(request, f"Funcionário '{emp.name}' cadastrado com sucesso!")
            return redirect('/employees/?tab=registered')
    else:
        form = RegisteredEmployeeForm()

    return render(request, 'employees/employee_form.html', {
        'form': form,
        'title': 'Cadastrar Novo Funcionário Registrado',
        'is_edit': False
    })


@tenant_required
@require_plan_feature('employees')
def registered_employee_edit(request, employee_id):
    emp = get_object_or_404(RegisteredEmployee, id=employee_id, company=request.company)
    if request.method == 'POST':
        form = RegisteredEmployeeForm(request.POST, instance=emp)
        if form.is_valid():
            form.save()
            messages.success(request, f"Dados do funcionário '{emp.name}' atualizados com sucesso!")
            return redirect('/employees/?tab=registered')
    else:
        form = RegisteredEmployeeForm(instance=emp)

    return render(request, 'employees/employee_form.html', {
        'form': form,
        'title': f"Editar Funcionário: {emp.name}",
        'is_edit': True,
        'employee': emp
    })


@tenant_required
@require_plan_feature('employees')
def registered_employee_toggle_status(request, employee_id):
    emp = get_object_or_404(RegisteredEmployee, id=employee_id, company=request.company)
    emp.is_active = not emp.is_active
    emp.save(update_fields=['is_active', 'updated_at'])
    if emp.is_active:
        messages.success(request, f"Funcionário '{emp.name}' agora está ATIVO. Alertas de folha de pagamento reativados.")
    else:
        messages.warning(request, f"Funcionário '{emp.name}' marcado como INATIVO. Não aparecerá mais nos alertas de pagamento e notificações.")
    return redirect('/employees/?tab=registered')


@tenant_required
@require_plan_feature('employees')
def salary_payment_create(request, employee_id):
    emp = get_object_or_404(RegisteredEmployee, id=employee_id, company=request.company)
    today = timezone.now().date()
    target_ref_month = get_previous_ref_month(today)

    if request.method == 'POST':
        form = SalaryPaymentForm(request.POST)
        if form.is_valid():
            ref_month = form.cleaned_data['reference_month']
            base_salary = form.cleaned_data['base_salary']
            bonus = form.cleaned_data['bonus']
            deductions = form.cleaned_data['deductions']
            payment_date = form.cleaned_data['payment_date']
            payment_method = form.cleaned_data['payment_method']
            notes = form.cleaned_data['notes']

            payment = record_salary_payment(
                employee=emp,
                reference_month=ref_month,
                base_salary=base_salary,
                bonus=bonus,
                deductions=deductions,
                payment_date=payment_date,
                payment_method=payment_method,
                notes=notes
            )
            messages.success(request, f"Pagamento de Salário ({ref_month}) de R$ {payment.total_paid} para {emp.name} efetuado com sucesso! Valor lançado como despesa no Livro Caixa.")
            return redirect('/employees/?tab=registered')
    else:
        form = SalaryPaymentForm(initial={
            'reference_month': target_ref_month,
            'base_salary': emp.monthly_salary,
            'bonus': Decimal('0.00'),
            'deductions': Decimal('0.00'),
            'payment_date': today.strftime('%Y-%m-%d'),
            'payment_method': 'pix',
        })

    return render(request, 'employees/salary_payment_form.html', {
        'form': form,
        'employee': emp,
        'title': f"Lançar Pagamento de Salário: {emp.name}"
    })
