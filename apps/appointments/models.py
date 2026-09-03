from django.db import models
from apps.saas_core.models import TenantModel

class Appointment(TenantModel):
    STATUS_CHOICES = [
        ('pending', 'Pendente de Confirmação'),
        ('confirmed', 'Confirmado'),
        ('arrived', 'Veículo no Pátio (OS Criada)'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
    ]

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Cliente'
    )
    vehicle = models.ForeignKey(
        'customers.Vehicle',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Veículo'
    )
    service_type = models.ForeignKey(
        'services.ServiceType',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Serviço Desejado'
    )
    preferred_employee = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_appointments',
        verbose_name='Operador Preferencial'
    )
    scheduled_date = models.DateField('Data Agendada')
    scheduled_time = models.TimeField('Horário Agendado')
    status = models.CharField('Status do Agendamento', max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField('Observações do Cliente', blank=True)

    order = models.OneToOneField(
        'orders.ServiceOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointment',
        verbose_name='Ordem de Serviço Gerada'
    )

    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
        ordering = ['scheduled_date', 'scheduled_time']

    def __str__(self):
        return f"{self.customer.name} - {self.vehicle.plate} ({self.scheduled_date} às {self.scheduled_time})"
