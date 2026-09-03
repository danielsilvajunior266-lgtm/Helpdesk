from django.db import transaction
from django.utils import timezone
from apps.finance.models import CashEntry, CashCategory

def create_cash_entry_from_order(order):
    """
    Cria uma entrada no livro caixa para uma ordem de serviço concluída de cliente avulso.
    """
    with transaction.atomic():
        # Obtém ou cria uma categoria padrão de receita de serviços
        category, _ = CashCategory.objects.get_or_create(
            company=order.company,
            name='Serviços Realizados',
            defaults={'category_type': 'income'}
        )

        entry = CashEntry.objects.create(
            company=order.company,
            description=f"OS #{order.id} - {order.service_type.name} ({order.vehicle.plate})",
            entry_type='income',
            amount=order.final_price,
            payment_method=order.payment_method or 'pix',
            category=category,
            order=order,
            entry_date=timezone.now().date()
        )
        return entry


def create_cash_entry_from_invoice(invoice, payment_method):
    """
    Cria uma entrada de receita no caixa quando uma fatura mensal de frota é liquidada.
    """
    with transaction.atomic():
        category, _ = CashCategory.objects.get_or_create(
            company=invoice.company,
            name='Faturamento Mensal (Frotas)',
            defaults={'category_type': 'income'}
        )

        entry = CashEntry.objects.create(
            company=invoice.company,
            description=f"Fatura Mensal #{invoice.id} - {invoice.customer.name} ({invoice.reference_month:02d}/{invoice.reference_year})",
            entry_type='income',
            amount=invoice.total_amount,
            payment_method=payment_method,
            category=category,
            entry_date=timezone.now().date()
        )
        return entry


def revert_cash_entry_for_order(order):
    """
    Remove ou estorna o lançamento de caixa caso a ordem seja cancelada.
    """
    with transaction.atomic():
        CashEntry.objects.filter(company=order.company, order=order).delete()
