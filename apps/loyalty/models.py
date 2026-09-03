from django.db import models
from apps.saas_core.models import TenantModel

class LoyaltyProgram(TenantModel):
    name = models.CharField('Nome do Programa', max_length=100, default='Clube Fidelidade')
    points_needed_for_reward = models.PositiveIntegerField('Pontos para Resgate', default=100)
    reward_description = models.CharField('Descrição da Recompensa', max_length=255, default='Lavagem Completa Grátis')
    points_per_service = models.PositiveIntegerField('Pontos Base por Serviço', default=10)
    is_active = models.BooleanField('Programa Ativo', default=True)

    class Meta:
        verbose_name = 'Programa de Fidelidade'
        verbose_name_plural = 'Programas de Fidelidade'

    def __str__(self):
        return f"{self.name} ({self.points_needed_for_reward} pts -> {self.reward_description})"


class LoyaltyAccount(TenantModel):
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='loyalty_accounts',
        verbose_name='Cliente'
    )
    points_balance = models.PositiveIntegerField('Saldo de Pontos', default=0)
    total_points_earned = models.PositiveIntegerField('Total Acumulado na História', default=0)
    total_rewards_redeemed = models.PositiveIntegerField('Recompensas Resgatadas', default=0)

    class Meta:
        verbose_name = 'Conta de Fidelidade'
        verbose_name_plural = 'Contas de Fidelidade'
        unique_together = ('company', 'customer')

    def __str__(self):
        return f"{self.customer.name} - Saldo: {self.points_balance} pts"


class LoyaltyEvent(TenantModel):
    EVENT_TYPE_CHOICES = [
        ('earned', 'Pontos Ganhos'),
        ('redeemed', 'Recompensa Resgatada'),
        ('reversed', 'Estorno de Pontos'),
    ]

    account = models.ForeignKey(
        LoyaltyAccount,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Conta de Fidelidade'
    )
    event_type = models.CharField('Tipo de Evento', max_length=20, choices=EVENT_TYPE_CHOICES)
    points = models.IntegerField('Quantidade de Pontos (+/-)')
    order = models.ForeignKey(
        'orders.ServiceOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loyalty_events',
        verbose_name='Ordem de Serviço (Origem)'
    )
    description = models.CharField('Descrição / Motivo', max_length=255)

    class Meta:
        verbose_name = 'Evento de Fidelidade'
        verbose_name_plural = 'Extrato de Fidelidade'
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.points > 0 else ''
        return f"{self.account.customer.name}: {sign}{self.points} pts ({self.description})"
