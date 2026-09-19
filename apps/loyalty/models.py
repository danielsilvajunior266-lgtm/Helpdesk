from django.db import models
from apps.saas_core.models import TenantModel

class LoyaltyProgram(TenantModel):
    REWARD_TYPE_CHOICES = [
        ('service', 'Serviço do Lava-Jato'),
        ('product', 'Produto / Brinde Personalizado'),
    ]

    name = models.CharField('Nome do Programa', max_length=100, default='Clube Fidelidade')
    reward_type = models.CharField('Tipo de Recompensa', max_length=20, choices=REWARD_TYPE_CHOICES, default='service')
    reward_service = models.ForeignKey(
        'services.ServiceType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loyalty_rewards',
        verbose_name='Serviço Recompensa Gratuito'
    )
    reward_product_name = models.CharField('Nome do Produto / Prêmio', max_length=255, blank=True)
    reward_description = models.CharField('Descrição da Recompensa', max_length=255, default='Lavagem Completa Grátis')
    points_needed_for_reward = models.PositiveIntegerField('Alvo de Pontos para Resgate', default=100)
    is_active = models.BooleanField('Programa Ativo', default=True)

    class Meta:
        verbose_name = 'Programa de Fidelidade'
        verbose_name_plural = 'Programas de Fidelidade'

    @property
    def reward_name(self):
        if self.reward_type == 'service' and self.reward_service:
            return self.reward_service.name
        elif self.reward_product_name:
            return self.reward_product_name
        elif self.reward_service:
            return self.reward_service.name
        return self.reward_description or 'Lavagem Completa Grátis'

    def __str__(self):
        return f"{self.name} ({self.points_needed_for_reward} pts -> {self.reward_name})"


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
        indexes = [
            models.Index(fields=['company', 'customer']),
        ]

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
        indexes = [
            models.Index(fields=['account', '-created_at']),
            models.Index(fields=['company', '-created_at']),
        ]

    def __str__(self):
        sign = '+' if self.points > 0 else ''
        return f"{self.account.customer.name}: {sign}{self.points} pts ({self.description})"
