from decimal import Decimal
from django.utils import timezone
from apps.finance.models import CashCategory, CashEntry
from apps.employees.models import SalaryPayment, DailyWork

def get_or_create_staff_category(company):
    """
    Retorna a categoria de despesa 'Salários e Diárias' para o Livro Caixa da empresa.
    """
    category, _ = CashCategory.objects.get_or_create(
        company=company,
        name='Salários e Diárias',
        defaults={'category_type': 'expense'}
    )
    return category


def record_salary_payment(employee, reference_month, base_salary, bonus=Decimal('0.00'), deductions=Decimal('0.00'), payment_date=None, payment_method='pix', notes=''):
    """
    Registra o pagamento mensal de salário de um funcionário fixo e debita automaticamente do Livro Caixa / PDV.
    """
    if payment_date is None:
        payment_date = timezone.now().date()

    base_salary = Decimal(str(base_salary))
    bonus = Decimal(str(bonus or 0))
    deductions = Decimal(str(deductions or 0))
    total_paid = base_salary + bonus - deductions

    company = employee.company
    category = get_or_create_staff_category(company)

    # 1. Cria a saída no Livro Caixa / PDV
    cash_entry = CashEntry.objects.create(
        company=company,
        description=f"Pagamento de Salário - {employee.name} (Ref: {reference_month})",
        entry_type='expense',
        amount=total_paid,
        payment_method=payment_method,
        category=category,
        entry_date=payment_date,
    )

    # 2. Cria o registro de pagamento
    payment = SalaryPayment.objects.create(
        company=company,
        employee=employee,
        reference_month=reference_month,
        base_salary=base_salary,
        bonus=bonus,
        deductions=deductions,
        total_paid=total_paid,
        payment_date=payment_date,
        payment_method=payment_method,
        status='paid',
        cash_entry=cash_entry,
        notes=notes
    )
    return payment


def pay_daily_work(daily_work, payment_method=None):
    """
    Dá baixa no pagamento de uma diária de ajudante e debita automaticamente do Livro Caixa / PDV.
    """
    if daily_work.status == 'paid':
        return daily_work

    company = daily_work.company
    category = get_or_create_staff_category(company)

    method = payment_method or daily_work.payment_method or 'pix'

    # 1. Cria a saída no Livro Caixa / PDV
    cash_entry = CashEntry.objects.create(
        company=company,
        description=f"Pagamento Diária - {daily_work.helper.name} (Data: {daily_work.work_date.strftime('%d/%m/%Y')})",
        entry_type='expense',
        amount=daily_work.daily_rate,
        payment_method=method,
        category=category,
        entry_date=timezone.now().date(),
    )

    # 2. Atualiza o status da diária
    daily_work.status = 'paid'
    daily_work.paid_at = timezone.now()
    daily_work.payment_method = method
    daily_work.cash_entry = cash_entry
    daily_work.save(update_fields=['status', 'paid_at', 'payment_method', 'cash_entry', 'updated_at'])

    return daily_work
