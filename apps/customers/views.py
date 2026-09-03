from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.saas_core.decorators import tenant_required
from apps.customers.models import Customer, Vehicle

@tenant_required
def customer_list(request):
    customers = Customer.objects.filter(company=request.company).prefetch_related('vehicles')
    return render(request, 'customers/list.html', {'customers': customers})


@tenant_required
def customer_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email', '')
        document = request.POST.get('document', '')
        billing_type = request.POST.get('billing_type', 'per_service')

        if not name or not phone:
            messages.error(request, 'Nome e Telefone são obrigatórios.')
            return redirect('customers:create')

        Customer.objects.create(
            company=request.company,
            name=name,
            phone=phone,
            email=email,
            document=document,
            billing_type=billing_type
        )
        messages.success(request, f'Cliente {name} cadastrado com sucesso!')
        return redirect('customers:list')

    return render(request, 'customers/form.html')


@tenant_required
def vehicle_create(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id, company=request.company)
    if request.method == 'POST':
        plate = request.POST.get('plate', '').strip().upper()
        brand = request.POST.get('brand', '')
        model = request.POST.get('model', '')
        color = request.POST.get('color', '')
        vehicle_type = request.POST.get('vehicle_type', 'sedan')

        if not plate or not brand or not model:
            messages.error(request, 'Placa, Marca e Modelo são obrigatórios.')
            return redirect('customers:list')

        if Vehicle.objects.filter(company=request.company, plate=plate).exists():
            messages.error(request, f'Já existe um veículo cadastrado com a placa {plate}.')
            return redirect('customers:list')

        Vehicle.objects.create(
            company=request.company,
            customer=customer,
            plate=plate,
            brand=brand,
            model=model,
            color=color,
            vehicle_type=vehicle_type
        )
        messages.success(request, f'Veículo {plate} adicionado para {customer.name}!')
        return redirect('customers:list')

    return render(request, 'customers/vehicle_form.html', {'customer': customer})
