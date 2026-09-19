from django.db import models
from django.utils import timezone
from apps.saas_core.models import TenantModel

class RegisteredEmployee(TenantModel):
    """
    Funcionário fixo contratado pelo lava-jato com remuneração mensal.
    """
    name = models.CharField('Nome Completo', max_length=150)
    role_title = models.CharField('Cargo / Função', max_length=100, default='Lavador / Detalhador')
    cpf = models.CharField('CPF', max_length=20, blank=True, null=True)
    phone = models.CharField('Telefone / WhatsApp', max_length=20, blank=True, null=True)
    monthly_salary = models.DecimalField('Salário Mensal Fixo (R$)', max_digits=10, decimal_places=2)
    payment_day = models.PositiveSmallIntegerField('Dia do Pagamento', default=5, help_text='Dia do mês para pagamento (ex: 5)')
    hire_date = models.DateField('Data de Admissão / Contratação', default=timezone.now)
    pix_key = models.CharField('Chave PIX para Pagamento', max_length=100, blank=True, null=True)
    is_active = models.BooleanField('Funcionário Ativo', default=True)
    notes = models.TextField('Observações Internas', blank=True, null=True)

    class Meta:
        verbose_name = 'Funcionário Registrado'
        verbose_name_plural = 'Funcionários Registrados'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.role_title} (R$ {self.monthly_salary})"


class SalaryPayment(TenantModel):
    """
    Histórico e controle de pagamento mensal de salário de funcionários fixos.
    """
    PAYMENT_METHOD_CHOICES = [
        ('pix', 'PIX'),
        ('cash', 'Dinheiro em Espécie'),
        ('bank_transfer', 'Transferência Bancária'),
        ('other', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('paid', 'Pago'),
        ('pending', 'Pendente'),
    ]

    employee = models.ForeignKey(
        RegisteredEmployee,
        on_delete=models.CASCADE,
        related_name='salary_payments',
        verbose_name='Funcionário'
    )
    reference_month = models.CharField('Mês de Referência', max_length=10, help_text='Ex: 03/2026')
    base_salary = models.DecimalField('Salário Base (R$)', max_digits=10, decimal_places=2)
    bonus = models.DecimalField('Bônus / Adicionais (R$)', max_digits=10, decimal_places=2, default=0.00)
    deductions = models.DecimalField('Descontos / Adiantamentos (R$)', max_digits=10, decimal_places=2, default=0.00)
    total_paid = models.DecimalField('Valor Total Pago (R$)', max_digits=10, decimal_places=2)
    payment_date = models.DateField('Data do Pagamento', default=timezone.now)
    payment_method = models.CharField('Forma de Pagamento', max_length=30, choices=PAYMENT_METHOD_CHOICES, default='pix')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='paid')
    cash_entry = models.ForeignKey(
        'finance.CashEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='salary_payments',
        verbose_name='Lançamento no Livro Caixa'
    )
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Pagamento de Salário'
        verbose_name_plural = 'Pagamentos de Salários'
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"Salário {self.employee.name} ({self.reference_month}) - R$ {self.total_paid}"


class DailyHelper(TenantModel):
    """
    Ajudante / Diarista cadastrado para diárias eventuais no lava-jato.
    """
    name = models.CharField('Nome do Ajudante', max_length=150)
    phone = models.CharField('Telefone / WhatsApp', max_length=20, blank=True, null=True)
    pix_key = models.CharField('Chave PIX', max_length=100, blank=True, null=True)
    notes = models.TextField('Observações / Especialidade', blank=True, null=True)

    class Meta:
        verbose_name = 'Ajudante Diário (Diarista)'
        verbose_name_plural = 'Ajudantes Diários (Diaristas)'
        ordering = ['name']

    def __str__(self):
        return self.name


class DailyWork(TenantModel):
    """
    Registro de diária trabalhada por um ajudante e respectivo pagamento.
    """
    SHIFT_CHOICES = [
        ('full_day', 'Dia Completo'),
        ('half_day', 'Meio Período'),
        ('night', 'Turno Noturno / Extra'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente de Pagamento'),
        ('paid', 'Pago ao Ajudante'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('pix', 'PIX'),
        ('cash', 'Dinheiro em Espécie'),
        ('bank_transfer', 'Transferência Bancária'),
        ('other', 'Outro'),
    ]

    helper = models.ForeignKey(
        DailyHelper,
        on_delete=models.CASCADE,
        related_name='works',
        verbose_name='Ajudante Diário'
    )
    work_date = models.DateField('Data do Trabalho', default=timezone.now)
    shift = models.CharField('Turno / Período', max_length=20, choices=SHIFT_CHOICES, default='full_day')
    daily_rate = models.DecimalField('Valor da Diária (R$)', max_digits=10, decimal_places=2)
    activity_description = models.CharField('Função / Atividade Realizada', max_length=200, default='Lavagem e secagem geral', blank=True)
    status = models.CharField('Status do Pagamento', max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField('Data e Hora da Baixa / Pagamento', null=True, blank=True)
    payment_method = models.CharField('Forma de Pagamento', max_length=30, choices=PAYMENT_METHOD_CHOICES, default='pix')
    cash_entry = models.ForeignKey(
        'finance.CashEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='daily_works',
        verbose_name='Lançamento no Livro Caixa'
    )
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Diária de Ajudante'
        verbose_name_plural = 'Diárias de Ajudantes'
        ordering = ['-work_date', '-created_at']

    def __str__(self):
        return f"{self.helper.name} em {self.work_date.strftime('%d/%m/%Y')} - R$ {self.daily_rate} ({self.get_status_display()})"
