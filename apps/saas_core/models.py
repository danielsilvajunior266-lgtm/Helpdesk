from django.db import models
from apps.core.models import TimeStampedModel

class Plan(TimeStampedModel):
    PLAN_CODES = [
        ('basic', 'Básico (Start)'),
        ('pro', 'Profissional (Pro)'),
        ('premium', 'Premium (Master)'),
    ]

    name = models.CharField('Nome do Plano', max_length=100)
    code = models.CharField('Código', max_length=20, choices=PLAN_CODES, unique=True)
    description = models.TextField('Descrição', blank=True)
    monthly_price = models.DecimalField('Valor Mensal (R$)', max_digits=10, decimal_places=2, default=0.00)
    max_users = models.PositiveIntegerField('Limite de Usuários/Operadores', default=1)

    # Feature Flags
    has_mobile_booking = models.BooleanField('Agendamento pelo App', default=True)
    has_loyalty = models.BooleanField('Programa de Fidelidade Digital', default=False)
    has_monthly_billing = models.BooleanField('Faturamento Mensal p/ Frotas', default=False)
    has_inspections = models.BooleanField('Vistoria com Fotos Antes/Depois', default=False)
    has_commissions = models.BooleanField('Comissões de Funcionários', default=False)
    has_push_notifications = models.BooleanField('Notificações Push no App', default=False)
    has_custom_reports = models.BooleanField('Relatórios Gerenciais Avançados (DRE)', default=False)

    class Meta:
        verbose_name = 'Plano SaaS'
        verbose_name_plural = 'Planos SaaS'
        ordering = ['monthly_price']

    def __str__(self):
        return f"{self.name} (R$ {self.monthly_price}/mês)"


class Company(TimeStampedModel):
    STATUS_CHOICES = [
        ('trial', 'Período de Testes'),
        ('active', 'Ativo'),
        ('past_due', 'Em Atraso'),
        ('blocked', 'Bloqueado'),
        ('cancelled', 'Cancelado'),
    ]

    name = models.CharField('Razão Social / Nome Fantasia', max_length=200)
    slug = models.SlugField('Identificador URL (Slug)', max_length=100, unique=True)
    document = models.CharField('CNPJ / CPF', max_length=20, blank=True)
    email = models.EmailField('E-mail Principal', blank=True)
    phone = models.CharField('Telefone / WhatsApp', max_length=20, blank=True)

    # Localização / Geolocalização para o App Mobile
    address = models.CharField('Endereço', max_length=255, blank=True)
    city = models.CharField('Cidade', max_length=100, blank=True)
    state = models.CharField('Estado (UF)', max_length=2, blank=True)
    latitude = models.DecimalField('Latitude', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Longitude', max_digits=9, decimal_places=6, null=True, blank=True)
    logo = models.ImageField('Logotipo', upload_to='company_logos/', blank=True, null=True)

    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='companies', verbose_name='Plano Contratado')
    status = models.CharField('Status da Empresa', max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        verbose_name = 'Empresa (Tenant)'
        verbose_name_plural = 'Empresas (Tenants)'
        ordering = ['name']

    def __str__(self):
        return self.name

    def has_feature(self, feature_name: str) -> bool:
        """
        Verifica se a empresa tem determinada funcionalidade ativa com base no seu plano.
        """
        if not self.plan:
            return False
        if feature_name in ['employees', 'has_employees']:
            return self.plan.code == 'premium' or getattr(self.plan, 'has_commissions', False)
        field_name = f"has_{feature_name}"
        return getattr(self.plan, field_name, False) or getattr(self.plan, feature_name, False)

    @property
    def is_operational(self) -> bool:
        return self.status in ['trial', 'active']


class Subscription(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('overdue', 'Atrasado'),
        ('cancelled', 'Cancelado'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='subscriptions', verbose_name='Empresa')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions', verbose_name='Plano')
    amount = models.DecimalField('Valor Cobrado', max_digits=10, decimal_places=2)
    due_date = models.DateField('Data de Vencimento')
    paid_at = models.DateTimeField('Data de Pagamento', null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        verbose_name = 'Assinatura SaaS'
        verbose_name_plural = 'Assinaturas SaaS'
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.company.name} - {self.plan.name} ({self.status})"


class TenantQuerySet(models.QuerySet):
    def for_company(self, company):
        if not company:
            return self.none()
        return self.filter(company=company)


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    pass


class TenantModel(TimeStampedModel):
    """
    Modelo base abstrato para todas as entidades vinculadas a um Tenant específico.
    Garante o isolamento lógico das empresas compartilhando o mesmo banco de dados.
    """
    company = models.ForeignKey(
        'saas_core.Company',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
        verbose_name='Empresa'
    )
    objects = TenantManager()

    class Meta:
        abstract = True
