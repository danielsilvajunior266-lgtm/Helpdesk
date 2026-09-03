from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from apps.saas_core.decorators import tenant_required
from apps.finance.models import CashEntry, CashCategory

@tenant_required
def cash_book(request):
    entries = CashEntry.objects.filter(company=request.company).select_related('category', 'order')[:100]
    categories = CashCategory.objects.filter(company=request.company)

    total_income = CashEntry.objects.filter(company=request.company, entry_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = CashEntry.objects.filter(company=request.company, entry_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expense

    return render(request, 'finance/cash_book.html', {
        'entries': entries,
        'categories': categories,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
    })


@tenant_required
def entry_create(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        entry_type = request.POST.get('entry_type')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method', 'pix')
        category_id = request.POST.get('category')

        if not description or not amount or not entry_type:
            messages.error(request, 'Preencha os campos obrigatórios.')
            return redirect('finance:cash_book')

        category = None
        if category_id:
            category = CashCategory.objects.filter(id=category_id, company=request.company).first()

        CashEntry.objects.create(
            company=request.company,
            description=description,
            entry_type=entry_type,
            amount=amount,
            payment_method=payment_method,
            category=category
        )
        messages.success(request, 'Lançamento registrado com sucesso!')
        return redirect('finance:cash_book')

    return redirect('finance:cash_book')
