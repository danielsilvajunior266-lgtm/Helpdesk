from django.db import models
from apps.saas_core.models import TenantModel

class ServiceOrder(TenantModel):
    STATUS_CHOICES = [
        ('waiting', 'Aguardando'),
        ('in_progress', 'Em Execução / Lavagem'),
        ('completed', 'Pronto / Finalizado'),
        ('delivered', 'Entregue ao Cliente'),
        ('cancelled', 'Cancelado'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('pix', 'PIX'),
        ('cash', 'Dinheiro em Espécie'),
        ('credit_card', 'Cartão de Crédito'),
        ('debit_card', 'Cartão de Débito'),
        ('monthly_invoice', 'Faturamento Mensal (Frota)'),
        ('pending', 'Pendente de Pagamento'),
    ]

    BILLING_STATUS_CHOICES = [
        ('NOT_APPLICABLE', 'Não Aplicável (Avulso)'),
        ('PENDING', 'Pendente de Fatura'),
        ('INVOICED', 'Faturado em Lote'),
        ('PAID', 'Fatura Paga'),
    ]

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Cliente'
    )
    vehicle = models.ForeignKey(
        'customers.Vehicle',
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Veículo'
    )
    service_type = models.ForeignKey(
        'services.ServiceType',
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Serviço Solicitado'
    )
    assigned_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders',
        verbose_name='Lavador / Responsável'
    )

    status = models.CharField('Status no Pátio', max_length=20, choices=STATUS_CHOICES, default='waiting')
    price = models.DecimalField('Preço Bruto (R$)', max_digits=10, decimal_places=2)
    discount = models.DecimalField('Desconto (R$)', max_digits=10, decimal_places=2, default=0.00)
    final_price = models.DecimalField('Preço Final (R$)', max_digits=10, decimal_places=2)

    payment_method = models.CharField('Forma de Pagamento', max_length=30, choices=PAYMENT_METHOD_CHOICES, default='pending')
    billing_status = models.CharField('Status de Faturamento', max_length=20, choices=BILLING_STATUS_CHOICES, default='NOT_APPLICABLE')

    notes = models.TextField('Observações / Instruções Especiais', blank=True)

    started_at = models.DateTimeField('Início do Atendimento', null=True, blank=True)
    completed_at = models.DateTimeField('Conclusão do Serviço', null=True, blank=True)
    delivered_at = models.DateTimeField('Entrega do Veículo', null=True, blank=True)

    class Meta:
        verbose_name = 'Ordem de Serviço'
        verbose_name_plural = 'Ordens de Serviço'
        ordering = ['-created_at']

    def __str__(self):
        return f"OS #{self.id} - {self.vehicle.plate} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.final_price:
            self.final_price = max(0, self.price - self.discount)
        super().save(*args, **kwargs)


class OrderPhoto(TenantModel):
    STAGE_CHOICES = [
        ('before', 'Antes (Entrada)'),
        ('after', 'Depois (Conclusão)'),
        ('damage', 'Avaria Prévia'),
    ]

    order = models.ForeignKey(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Ordem de Serviço'
    )
    stage = models.CharField('Etapa da Foto', max_length=20, choices=STAGE_CHOICES, default='before')
    image = models.ImageField('Imagem da Vistoria', upload_to='order_inspections/')
    caption = models.CharField('Legenda / Observação', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Foto da Vistoria'
        verbose_name_plural = 'Fotos da Vistoria'
        ordering = ['stage', 'created_at']

    def __str__(self):
        return f"Foto OS #{self.order_id} ({self.get_stage_display()})"
