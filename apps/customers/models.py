from django.db import models
from apps.saas_core.models import TenantModel

class Customer(TenantModel):
    BILLING_TYPE_CHOICES = [
        ('per_service', 'Avulso (Pagamento por Serviço)'),
        ('monthly', 'Faturamento Mensal / Frota'),
    ]

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_profiles',
        verbose_name='Usuário App Mobile'
    )
    name = models.CharField('Nome do Cliente / Razão Social', max_length=150)
    phone = models.CharField('Telefone / WhatsApp', max_length=20)
    email = models.EmailField('E-mail', blank=True)
    document = models.CharField('CPF / CNPJ', max_length=20, blank=True)
    billing_type = models.CharField('Tipo de Faturamento', max_length=20, choices=BILLING_TYPE_CHOICES, default='per_service')
    notes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_billing_type_display()})"


class Vehicle(TenantModel):
    VEHICLE_TYPE_CHOICES = [
        ('hatch', 'Hatch'),
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('pickup', 'Picape'),
        ('moto', 'Motocicleta'),
        ('van', 'Van / Utilitário'),
        ('truck', 'Caminhão'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='vehicles', verbose_name='Proprietário')
    plate = models.CharField('Placa', max_length=10)
    brand = models.CharField('Marca / Fabricante', max_length=50)
    model = models.CharField('Modelo', max_length=50)
    color = models.CharField('Cor', max_length=30, blank=True)
    vehicle_type = models.CharField('Porte / Tipo', max_length=20, choices=VEHICLE_TYPE_CHOICES, default='sedan')
    photo = models.ImageField('Foto do Veículo', upload_to='vehicles/', blank=True, null=True)

    class Meta:
        verbose_name = 'Veículo'
        verbose_name_plural = 'Veículos'
        unique_together = ('company', 'plate')
        ordering = ['brand', 'model']

    def __str__(self):
        return f"{self.brand} {self.model} - {self.plate.upper()}"

    def save(self, *args, **kwargs):
        self.plate = self.plate.strip().upper()
        super().save(*args, **kwargs)
