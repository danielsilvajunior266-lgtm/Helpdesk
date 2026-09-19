from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.saas_core.decorators import tenant_required, require_plan_feature
from apps.billing.models import MonthlyInvoice
from apps.customers.models import Customer
from apps.billing.services import generate_monthly_invoice, mark_invoice_paid

from django.db.models import Count, Sum
from apps.orders.models import ServiceOrder

@tenant_required
@require_plan_feature('monthly_billing')
def invoice_list(request):
    invoices = MonthlyInvoice.objects.filter(company=request.company).select_related('customer').prefetch_related('items').order_by('-reference_year', '-reference_month', '-id')
    fleet_customers = Customer.objects.filter(company=request.company, billing_type='monthly').prefetch_related('vehicles')
    regular_customers = Customer.objects.filter(company=request.company, billing_type='per_service').prefetch_related('vehicles').order_by('name')

    # Calcula ordens concluídas acumuladas e pendentes de fatura para cada frotista
    pending_stats = ServiceOrder.objects.filter(
        company=request.company,
        status__in=['completed', 'delivered'],
        billing_status='PENDING'
    ).values('customer_id').annotate(
        pending_count=Count('id'),
        pending_total=Sum('final_price')
    )
    pending_dict = {item['customer_id']: item for item in pending_stats}

    fleet_customers_data = []
    total_unbilled_fleet_amount = 0
    total_unbilled_orders_count = 0

    for fc in fleet_customers:
        stat = pending_dict.get(fc.id, {'pending_count': 0, 'pending_total': 0})
        p_count = stat['pending_count']
        p_total = stat['pending_total'] or 0
        total_unbilled_orders_count += p_count
        total_unbilled_fleet_amount += p_total

        fleet_customers_data.append({
            'customer': fc,
            'pending_count': p_count,
            'pending_total': p_total,
            'vehicles_count': fc.vehicles.count(),
            'vehicles_sample': list(fc.vehicles.all()[:3])
        })

    return render(request, 'billing/list.html', {
        'invoices': invoices,
        'fleet_customers': fleet_customers,
        'fleet_customers_data': fleet_customers_data,
        'regular_customers': regular_customers,
        'total_unbilled_fleet_amount': total_unbilled_fleet_amount,
        'total_unbilled_orders_count': total_unbilled_orders_count,
    })


@tenant_required
@require_plan_feature('monthly_billing')
def add_fleet_customer(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        if not customer_id:
            messages.error(request, 'Por favor, selecione um cliente cadastrado para transformar em frotista.')
            return redirect('billing:list')

        customer = get_object_or_404(Customer, id=customer_id, company=request.company)
        customer.billing_type = 'monthly'
        customer.save()
        messages.success(request, f'🎉 O cliente "{customer.name}" agora é um Frotista oficial! Todas as próximas ordens concluídas serão acumuladas para faturamento mensal consolidado.')
        return redirect('billing:list')

    return redirect('billing:list')


@tenant_required
@require_plan_feature('monthly_billing')
def remove_fleet_customer(request, customer_id):
    if request.method == 'POST':
        customer = get_object_or_404(Customer, id=customer_id, company=request.company)
        customer.billing_type = 'per_service'
        customer.save()
        messages.info(request, f'O cliente "{customer.name}" retornou ao modo Avulso (pagamento por serviço).')
        return redirect('billing:list')

    return redirect('billing:list')


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
