from django.shortcuts import render, redirect
from django.contrib import messages
from apps.saas_core.decorators import tenant_required
from apps.services.models import ServiceCategory, ServiceType

@tenant_required
def service_list(request):
    services = ServiceType.objects.filter(company=request.company).select_related('category')
    categories = ServiceCategory.objects.filter(company=request.company)
    return render(request, 'services/list.html', {'services': services, 'categories': categories})


@tenant_required
def service_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('default_price')
        duration = request.POST.get('estimated_duration_minutes', 45)
        category_id = request.POST.get('category')
        description = request.POST.get('description', '')

        if not name or not price:
            messages.error(request, 'Nome e Preço são obrigatórios.')
            return redirect('services:create')

        category = None
        if category_id:
            category = ServiceCategory.objects.filter(id=category_id, company=request.company).first()

        counts_for_loyalty = request.POST.get('counts_for_loyalty') == 'on'
        loyalty_points = request.POST.get('loyalty_points_earned', 10)

        try:
            loyalty_points = max(0, int(loyalty_points))
        except ValueError:
            loyalty_points = 10

        ServiceType.objects.create(
            company=request.company,
            name=name,
            default_price=price,
            estimated_duration_minutes=duration,
            category=category,
            description=description,
            counts_for_loyalty=counts_for_loyalty,
            loyalty_points_earned=loyalty_points
        )
        messages.success(request, f'Serviço {name} cadastrado com sucesso!')
        return redirect('services:list')

    categories = ServiceCategory.objects.filter(company=request.company)
    return render(request, 'services/form.html', {'categories': categories})
