from django.db import transaction
from django.utils import timezone
from datetime import date
from apps.billing.models import MonthlyInvoice, MonthlyInvoiceItem
from apps.orders.models import ServiceOrder

def generate_monthly_invoice(company, customer, year: int, month: int, due_date: date = None) -> MonthlyInvoice:
    """
    Consolida todas as ordens de serviço pendentes de faturamento de um cliente frotista
    em uma fatura mensal com snapshot imutável dos itens.
    """
    with transaction.atomic():
        if not due_date:
            # Padrão: dia 10 do mês seguinte
            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1
            due_date = date(next_year, next_month, 10)

        # Localiza ordens concluídas pendentes de fatura
        orders = ServiceOrder.objects.select_for_update().filter(
            company=company,
            customer=customer,
            status__in=['completed', 'delivered'],
            billing_status='PENDING'
        )

        if not orders.exists():
            raise ValueError(f"Não há ordens de serviço pendentes de faturamento para o cliente {customer.name}.")

        total_amount = sum(order.final_price for order in orders)

        invoice, created = MonthlyInvoice.objects.get_or_create(
            company=company,
            customer=customer,
            reference_month=month,
            reference_year=year,
            defaults={
                'total_amount': total_amount,
                'due_date': due_date,
                'status': 'open'
            }
        )

        if not created:
            # Atualiza valor se a fatura já existia em aberto
            invoice.total_amount += total_amount
            invoice.save()

        # Cria os snapshots imutáveis e marca as ordens como INVOICED
        for order in orders:
            MonthlyInvoiceItem.objects.create(
                company=company,
                invoice=invoice,
                order=order,
                vehicle_plate=order.vehicle.plate,
                service_name=order.service_type.name,
                service_date=order.completed_at or order.created_at,
                amount=order.final_price
            )
            order.billing_status = 'INVOICED'
            order.save()

        return invoice


def mark_invoice_paid(invoice: MonthlyInvoice, payment_method: str = 'pix') -> MonthlyInvoice:
    """
    Liquida a fatura, marca ordens vinculadas como PAID e gera entrada correspondente no caixa.
    """
    with transaction.atomic():
        invoice = MonthlyInvoice.objects.select_for_update().get(id=invoice.id)
        if invoice.status == 'paid':
            return invoice

        invoice.status = 'paid'
        invoice.paid_at = timezone.now()
        invoice.save()

        # Atualiza status das ordens do lote para PAID
        orders_ids = invoice.items.values_list('order_id', flat=True)
        ServiceOrder.objects.filter(id__in=orders_ids).update(billing_status='PAID')

        # Lazy import para gerar receita no Livro Caixa
        from apps.finance.services import create_cash_entry_from_invoice
        create_cash_entry_from_invoice(invoice, payment_method)

        return invoice


def cancel_invoice(invoice: MonthlyInvoice) -> MonthlyInvoice:
    """
    Cancela uma fatura e retorna as ordens vinculadas para o status PENDING.
    """
    with transaction.atomic():
        invoice = MonthlyInvoice.objects.select_for_update().get(id=invoice.id)
        if invoice.status == 'paid':
            raise ValueError("Não é possível cancelar uma fatura que já foi liquidada.")

        orders_ids = invoice.items.values_list('order_id', flat=True)
        ServiceOrder.objects.filter(id__in=orders_ids).update(billing_status='PENDING')

        invoice.status = 'cancelled'
        invoice.save()
        return invoice
