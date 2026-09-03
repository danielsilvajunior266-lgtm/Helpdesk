from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.saas_core.decorators import tenant_required, require_plan_feature
from apps.billing.models import MonthlyInvoice
from apps.customers.models import Customer
from apps.billing.services import generate_monthly_invoice, mark_invoice_paid

@tenant_required
@require_plan_feature('monthly_billing')
def invoice_list(request):
    invoices = MonthlyInvoice.objects.filter(company=request.company).select_related('customer')
    fleet_customers = Customer.objects.filter(company=request.company, billing_type='monthly')
    return render(request, 'billing/list.html', {
        'invoices': invoices,
        'fleet_customers': fleet_customers,
    })


@tenant_required
@require_plan_feature('monthly_billing')
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(
        MonthlyInvoice.objects.prefetch_related('items__order__vehicle'),
        id=invoice_id,
        company=request.company
    )
    return render(request, 'billing/detail.html', {'invoice': invoice})


@tenant_required
@require_plan_feature('monthly_billing')
def invoice_generate(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))

        customer = get_object_or_404(Customer, id=customer_id, company=request.company)

        try:
            invoice = generate_monthly_invoice(request.company, customer, year, month)
            messages.success(request, f"Fatura #{invoice.id} gerada com sucesso no valor de R$ {invoice.total_amount}!")
            return redirect('billing:detail', invoice_id=invoice.id)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('billing:list')

    return redirect('billing:list')


@tenant_required
@require_plan_feature('monthly_billing')
def invoice_mark_paid(request, invoice_id):
    invoice = get_object_or_404(MonthlyInvoice, id=invoice_id, company=request.company)
    payment_method = request.POST.get('payment_method', 'pix')
    mark_invoice_paid(invoice, payment_method=payment_method)
    messages.success(request, f"Fatura #{invoice.id} marcada como liquidada!")
    return redirect('billing:detail', invoice_id=invoice.id)
