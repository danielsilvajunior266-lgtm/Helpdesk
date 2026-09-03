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

    @property
    def is_vip(self) -> bool:
        """
        Regra de Fidelidade VIP do Estabelecimento:
        1. O cliente atinge o status VIP quando leva o veículo ao menos 1 vez por mês
           durante 3 meses consecutivos em ordens de serviço concluídas ('completed')
           neste lava-jato específico.
        2. Perda de VIP: Se o cliente ficar 2 meses ou mais sem realizar nenhuma lavagem/serviço,
           o status e a insígnia VIP desaparecem para o dono do lava-jato.
        """
        from apps.orders.models import ServiceOrder
        from django.utils import timezone

        completed_orders = ServiceOrder.objects.filter(
            customer=self,
            company=self.company,
            status='completed'
        ).order_by('created_at')

        if not completed_orders.exists():
            return False

        # Extrair anos e meses únicos de visitas
        # Representamos cada mês como um índice linear: ano * 12 + mês
        visit_months = sorted(list(set(
            order.created_at.year * 12 + order.created_at.month
            for order in completed_orders
        )))

        # Verificar se houve ao menos uma sequência de 3 meses consecutivos
        has_consecutive_3_months = False
        consecutive_count = 1
        for i in range(1, len(visit_months)):
            if visit_months[i] == visit_months[i - 1] + 1:
                consecutive_count += 1
                if consecutive_count >= 3:
                    has_consecutive_3_months = True
            elif visit_months[i] == visit_months[i - 1]:
                continue
            else:
                consecutive_count = 1

        if not has_consecutive_3_months:
            return False

        # Verificar inatividade (2 meses ou mais sem visitar)
        last_order = completed_orders.last()
        if not last_order:
            return False

        now = timezone.now()
        current_month_index = now.year * 12 + now.month
        last_visit_month_index = last_order.created_at.year * 12 + last_order.created_at.month

        months_since_last_visit = current_month_index - last_visit_month_index

        if months_since_last_visit >= 2:
            return False

        return True


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
