from django.db import models
from apps.saas_core.models import TenantModel

class ServiceCategory(TenantModel):
    name = models.CharField('Nome da Categoria', max_length=100)
    description = models.TextField('Descrição', blank=True)
    icon = models.CharField('Ícone (ex: spark, car, brush)', max_length=50, default='spark')

    class Meta:
        verbose_name = 'Categoria de Serviço'
        verbose_name_plural = 'Categorias de Serviços'
        ordering = ['name']

    def __str__(self):
        return self.name


class ServiceType(TenantModel):
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services',
        verbose_name='Categoria'
    )
    name = models.CharField('Nome do Serviço', max_length=150)
    description = models.TextField('Descrição', blank=True)
    default_price = models.DecimalField('Preço Padrão (R$)', max_digits=10, decimal_places=2)
    estimated_duration_minutes = models.PositiveIntegerField('Duração Estimada (minutos)', default=45)
    counts_for_loyalty = models.BooleanField('Pontua na Fidelidade', default=True)
    loyalty_points_earned = models.PositiveIntegerField('Pontos Concedidos', default=10)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Tipo de Serviço'
        verbose_name_plural = 'Tipos de Serviços'
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} - R$ {self.default_price}"
