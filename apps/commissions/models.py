from django.db import models
from apps.saas_core.models import TenantModel

class CommissionRule(TenantModel):
    CALC_TYPE_CHOICES = [
        ('percentage', 'Porcentagem (%)'),
        ('fixed', 'Valor Fixo (R$)'),
    ]

    service_type = models.ForeignKey(
        'services.ServiceType',
        on_delete=models.CASCADE,
        related_name='commission_rules',
        verbose_name='Serviço'
    )
    calc_type = models.CharField('Tipo de Cálculo', max_length=20, choices=CALC_TYPE_CHOICES, default='percentage')
    value = models.DecimalField('Valor ou Percentual', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Regra de Comissão'
        verbose_name_plural = 'Regras de Comissão'
        unique_together = ('company', 'service_type')

    def __str__(self):
        rule_str = f"{self.value}%" if self.calc_type == 'percentage' else f"R$ {self.value}"
        return f"{self.service_type.name} -> {rule_str}"


class EmployeeCommission(TenantModel):
    STATUS_CHOICES = [
        ('pending', 'Pendente de Pagamento'),
        ('paid', 'Pago ao Funcionário'),
    ]

    employee = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='commissions',
        verbose_name='Funcionário / Lavador'
    )
    order = models.OneToOneField(
        'orders.ServiceOrder',
        on_delete=models.CASCADE,
        related_name='commission',
        verbose_name='Ordem de Serviço (Origem)'
    )
    amount = models.DecimalField('Valor da Comissão (R$)', max_digits=10, decimal_places=2)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField('Data do Pagamento', null=True, blank=True)

    class Meta:
        verbose_name = 'Comissão de Funcionário'
        verbose_name_plural = 'Comissões de Funcionários'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.get_full_name() or self.employee.username}: R$ {self.amount} (OS #{self.order_id})"
