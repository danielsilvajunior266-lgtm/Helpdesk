from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from apps.saas_core.decorators import tenant_required, require_plan_feature
from apps.orders.models import ServiceOrder, OrderPhoto
from apps.customers.models import Customer, Vehicle
from apps.services.models import ServiceType
from apps.accounts.models import User
from apps.orders.services import (
    start_service_order,
    complete_service_order,
    deliver_service_order,
    cancel_service_order
)

@tenant_required
def kanban_view(request):
    company = request.company
    orders = ServiceOrder.objects.filter(company=company).select_related('customer', 'vehicle', 'service_type', 'assigned_to')

    waiting_orders = orders.filter(status='waiting')
    in_progress_orders = orders.filter(status='in_progress')
    completed_orders = orders.filter(status='completed')
    
    # Entregues recentes (últimas 24h)
    delivered_orders = orders.filter(status='delivered').order_by('-delivered_at')[:15]

    context = {
        'waiting_orders': waiting_orders,
        'in_progress_orders': in_progress_orders,
        'completed_orders': completed_orders,
        'delivered_orders': delivered_orders,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'orders/partials/kanban_board.html', context)

    return render(request, 'orders/kanban.html', context)


@tenant_required
def order_create(request):
    company = request.company
    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle')
        service_type_id = request.POST.get('service_type')
        assigned_to_id = request.POST.get('assigned_to')
        custom_price = request.POST.get('price')
        discount = request.POST.get('discount', '0')
        notes = request.POST.get('notes', '')

        vehicle = get_object_or_404(Vehicle, id=vehicle_id, company=company)
        service = get_object_or_404(ServiceType, id=service_type_id, company=company)
        assigned_to = User.objects.filter(id=assigned_to_id, company=company).first() if assigned_to_id else None

        price = float(custom_price) if custom_price else float(service.default_price)
        discount_val = float(discount) if discount else 0.0
        final_price = max(0.0, price - discount_val)

        order = ServiceOrder.objects.create(
            company=company,
            customer=vehicle.customer,
            vehicle=vehicle,
            service_type=service,
            assigned_to=assigned_to,
            price=price,
            discount=discount_val,
            final_price=final_price,
            notes=notes,
            status='waiting'
        )

        messages.success(request, f'Ordem de Serviço #{order.id} aberta para {vehicle.plate}!')
        return redirect('orders:kanban')

    vehicles = Vehicle.objects.filter(company=company).select_related('customer')
    services = ServiceType.objects.filter(company=company, is_active=True)
    employees = User.objects.filter(company=company, role__in=['employee', 'owner'])

    return render(request, 'orders/form.html', {
        'vehicles': vehicles,
        'services': services,
        'employees': employees,
    })


@tenant_required
def update_status(request, order_id):
    order = get_object_or_404(ServiceOrder, id=order_id, company=request.company)
    target_status = request.POST.get('status') or request.GET.get('status')
    payment_method = request.POST.get('payment_method') or 'pix'

    if target_status == 'in_progress':
        start_service_order(order, assigned_to=request.user)
    elif target_status == 'completed':
        complete_service_order(order, payment_method=payment_method)
    elif target_status == 'delivered':
        deliver_service_order(order)
    elif target_status == 'cancelled':
        cancel_service_order(order)

    # Re-renderiza o quadro Kanban completo para requisições HTMX
    if request.headers.get('HX-Request'):
        orders = ServiceOrder.objects.filter(company=request.company).select_related('customer', 'vehicle', 'service_type', 'assigned_to')
        return render(request, 'orders/partials/kanban_board.html', {
            'waiting_orders': orders.filter(status='waiting'),
            'in_progress_orders': orders.filter(status='in_progress'),
            'completed_orders': orders.filter(status='completed'),
            'delivered_orders': orders.filter(status='delivered').order_by('-delivered_at')[:15],
        })

    return redirect('orders:kanban')


@tenant_required
def order_detail(request, order_id):
    order = get_object_or_404(
        ServiceOrder.objects.select_related('customer', 'vehicle', 'service_type', 'assigned_to'),
        id=order_id,
        company=request.company
    )
    photos = order.photos.all()
    return render(request, 'orders/detail.html', {'order': order, 'photos': photos})


@tenant_required
@require_plan_feature('inspections')
def upload_photo(request, order_id):
    order = get_object_or_404(ServiceOrder, id=order_id, company=request.company)
    if request.method == 'POST' and request.FILES.get('image'):
        stage = request.POST.get('stage', 'before')
        caption = request.POST.get('caption', '')
        OrderPhoto.objects.create(
            company=request.company,
            order=order,
            stage=stage,
            image=request.FILES['image'],
            caption=caption
        )
        messages.success(request, 'Foto da vistoria adicionada com sucesso!')
    return redirect('orders:detail', order_id=order.id)
