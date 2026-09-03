from django.db import models
from django.utils import timezone
from apps.saas_core.models import TenantModel

class CashCategory(TenantModel):
    TYPE_CHOICES = [
        ('income', 'Receita / Entrada'),
        ('expense', 'Despesa / Saída'),
    ]

    name = models.CharField('Nome da Categoria', max_length=100)
    category_type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES, default='income')

    class Meta:
        verbose_name = 'Categoria do Caixa'
        verbose_name_plural = 'Categorias do Caixa'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class CashEntry(TenantModel):
    ENTRY_TYPE_CHOICES = [
        ('income', 'Receita / Entrada'),
        ('expense', 'Despesa / Saída'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('pix', 'PIX'),
        ('cash', 'Dinheiro em Espécie'),
        ('credit_card', 'Cartão de Crédito'),
        ('debit_card', 'Cartão de Débito'),
        ('bank_transfer', 'Transferência Bancária'),
        ('monthly_invoice', 'Faturamento Mensal / Boleto'),
        ('other', 'Outro'),
    ]

    description = models.CharField('Descrição do Lançamento', max_length=255)
    entry_type = models.CharField('Tipo', max_length=20, choices=ENTRY_TYPE_CHOICES)
    amount = models.DecimalField('Valor (R$)', max_digits=10, decimal_places=2)
    payment_method = models.CharField('Forma de Pagamento', max_length=30, choices=PAYMENT_METHOD_CHOICES, default='pix')
    category = models.ForeignKey(
        CashCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entries',
        verbose_name='Categoria'
    )
    order = models.ForeignKey(
        'orders.ServiceOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cash_entries',
        verbose_name='Ordem de Serviço (Origem)'
    )
    entry_date = models.DateField('Data do Lançamento', default=timezone.now)

    class Meta:
        verbose_name = 'Lançamento de Caixa'
        verbose_name_plural = 'Livro Caixa'
        ordering = ['-entry_date', '-created_at']

    def __str__(self):
        sign = '+' if self.entry_type == 'income' else '-'
        return f"[{self.entry_date}] {sign} R$ {self.amount} - {self.description}"
