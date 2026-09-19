from django.db import models
from apps.saas_core.models import TenantModel

class MonthlyInvoice(TenantModel):
    STATUS_CHOICES = [
        ('open', 'Aberta'),
        ('paid', 'Liquidada'),
        ('cancelled', 'Cancelada'),
    ]

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='monthly_invoices',
        verbose_name='Cliente Frotista'
    )
    reference_month = models.PositiveSmallIntegerField('Mês de Referência (1-12)')
    reference_year = models.PositiveSmallIntegerField('Ano de Referência')
    total_amount = models.DecimalField('Valor Total Consolidado (R$)', max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField('Status da Fatura', max_length=20, choices=STATUS_CHOICES, default='open')
    due_date = models.DateField('Data de Vencimento')
    paid_at = models.DateTimeField('Data da Liquidação', null=True, blank=True)

    class Meta:
        verbose_name = 'Fatura Mensal'
        verbose_name_plural = 'Faturas Mensais'
        unique_together = ('company', 'customer', 'reference_month', 'reference_year')
        ordering = ['-reference_year', '-reference_month']

    def __str__(self):
        return f"Fatura #{self.id} - {self.customer.name} ({self.reference_month:02d}/{self.reference_year}) - R$ {self.total_amount}"


class MonthlyInvoiceItem(TenantModel):
    invoice = models.ForeignKey(
        MonthlyInvoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Fatura'
    )
    order = models.OneToOneField(
        'orders.ServiceOrder',
        on_delete=models.PROTECT,
        related_name='invoice_item',
        verbose_name='Ordem de Serviço (Origem)'
    )
    vehicle_plate = models.CharField('Placa do Veículo', max_length=15)
    service_name = models.CharField('Serviço Executado', max_length=150)
    service_date = models.DateTimeField('Data do Atendimento')
    amount = models.DecimalField('Valor Cobrado (R$)', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item da Fatura'
        verbose_name_plural = 'Itens da Fatura'
        ordering = ['service_date']

    def __str__(self):
        return f"{self.vehicle_plate} - {self.service_name} (R$ {self.amount})"
