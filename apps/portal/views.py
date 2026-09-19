import json
from datetime import datetime, date, time
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Prefetch

from apps.saas_core.models import Company
from apps.customers.models import Customer, Vehicle
from apps.services.models import ServiceType, ServiceCategory
from apps.orders.models import ServiceOrder, OrderPhoto
from apps.appointments.models import Appointment
from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount, LoyaltyEvent


def get_active_company(request):
    """
    Recupera a empresa ativa selecionada para a sessão do cliente no portal.
    """
    company_id = request.GET.get('company_id') or request.session.get('selected_company_id')
    company = None

    if company_id and str(company_id).isdigit():
        company = Company.objects.filter(id=int(company_id), status='active').select_related('plan').first()
        if company:
            request.session['selected_company_id'] = company.id

    if not company:
        if request.user.is_authenticated and getattr(request.user, 'company', None):
            company = request.user.company
        else:
            company = Company.objects.filter(status='active').select_related('plan').first()
        
        if company:
            request.session['selected_company_id'] = company.id

    return company


def portal_select_company(request):
    """
    Tela inicial de busca e seleção de Lava-Jato para o cliente.
    Apresenta barra de busca em tempo real, destaque do último lava-jato visitado,
    catálogo de parceiros credenciados e visão global de atendimento dos veículos do cliente.
    """
    search_query = request.GET.get('q', '').strip()
    companies = Company.objects.filter(status='active').select_related('plan')

    if search_query:
        from django.db.models import Q
        companies = companies.filter(
            Q(name__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(state__icontains=search_query)
        )

    last_visited_company = None
    last_order = None
    last_appointment = None
    vehicles = []
    active_orders = []
    recent_orders = []
    appointments = []
    loyalty_accounts = []
    customer = None

    if request.user.is_authenticated:
        from apps.orders.services import get_user_service_orders
        customer = Customer.objects.filter(user=request.user).first()
        vehicles = Vehicle.objects.filter(customer__user=request.user).select_related('company', 'customer').distinct()

        all_orders = get_user_service_orders(request.user)

        active_orders = [o for o in all_orders if o.status not in ['delivered', 'cancelled']]
        recent_orders = [o for o in all_orders if o.status in ['delivered', 'completed']][:10]

        appointments = Appointment.objects.filter(
            customer__user=request.user
        ).select_related('company', 'vehicle', 'service_type', 'customer').order_by('-scheduled_date', '-scheduled_time')

        loyalty_accounts = LoyaltyAccount.objects.filter(
            customer__user=request.user
        ).select_related('company', 'company__plan', 'customer').prefetch_related(
            Prefetch('events', queryset=LoyaltyEvent.objects.order_by('-created_at'))
        )

        last_order = all_orders.first() if hasattr(all_orders, 'first') else (all_orders[0] if active_orders else None)
        last_appointment = appointments.first()

        if last_order:
            last_visited_company = last_order.company
        elif last_appointment:
            last_visited_company = last_appointment.company
        elif request.session.get('last_visited_company_id'):
            last_visited_company = Company.objects.filter(id=request.session['last_visited_company_id'], status='active').first()
        elif getattr(request.user, 'company', None):
            last_visited_company = request.user.company

    context = {
        'companies': companies,
        'search_query': search_query,
        'last_visited_company': last_visited_company,
        'last_order': last_order,
        'last_appointment': last_appointment,
        'vehicles': vehicles,
        'active_orders': active_orders,
        'recent_orders': recent_orders,
        'appointments': appointments,
        'loyalty_accounts': loyalty_accounts,
        'customer': customer,
        'active_tab': request.GET.get('tab', 'home'),
        'is_select_company_page': True,
    }
    return render(request, 'portal/select_company.html', context)


def portal_switch_company(request, company_id):
    """
    Altera a empresa parceira selecionada no portal web.
    """
    company = get_object_or_404(Company, id=company_id, status='active')
    request.session['selected_company_id'] = company.id
    request.session['last_visited_company_id'] = company.id
    messages.info(request, f"Lava-jato selecionado: {company.name}")
    next_url = request.GET.get('next') or 'portal:home'
    return redirect(next_url)


def portal_home(request):
    """
    Página principal do Portal Web do Cliente (Motorista).
    Totalmente responsiva para Mobile (estilo app), Tablet e PC.
    """
    companies = Company.objects.filter(status='active').select_related('plan')
    company = get_active_company(request)

    services = []
    vehicles = []
    active_orders = []
    recent_orders = []
    appointments = []
    loyalty_account = None
    customer = None

    if company:
        services = ServiceType.objects.filter(company=company, is_active=True).select_related('category').order_by('default_price')

        if request.user.is_authenticated:
            from apps.orders.services import get_user_service_orders
            # Obtém ou inicializa perfil de cliente para este usuário
            customer = Customer.objects.filter(user=request.user, company=company).first()
            if not customer:
                customer = Customer.objects.filter(user=request.user).first()

            # Veículos do cliente
            vehicles = Vehicle.objects.filter(customer__user=request.user).select_related('company', 'customer').distinct()

            # Ordens de serviço ativas no pátio e concluídas recentemente
            all_orders = get_user_service_orders(request.user, company=company)

            active_orders = [o for o in all_orders if o.status not in ['delivered', 'cancelled']]
            recent_orders = [o for o in all_orders if o.status in ['delivered', 'completed']][:5]

            # Agendamentos do cliente
            appointments = Appointment.objects.filter(
                customer__user=request.user
            ).select_related('company', 'vehicle', 'service_type', 'customer').order_by('-scheduled_date', '-scheduled_time')

            # Saldo e programa de fidelidade
            if company.has_feature('loyalty'):
                loyalty_account = LoyaltyAccount.objects.filter(
                    customer__user=request.user,
                    company=company
                ).select_related('customer', 'company').prefetch_related(
                    Prefetch('events', queryset=LoyaltyEvent.objects.order_by('-created_at'))
                ).first()

    # Cálculo da meta de fidelidade
    loyalty_program = LoyaltyProgram.objects.filter(company=company, is_active=True).first() if company else None
    loyalty_target = loyalty_program.points_needed_for_reward if loyalty_program else 100
    reward_description = loyalty_program.reward_description if loyalty_program else "Lavagem Completa Grátis"
    loyalty_progress = 0
    if loyalty_account and loyalty_target > 0:
        loyalty_progress = min(100, int((loyalty_account.points_balance / loyalty_target) * 100))

    context = {
        'companies': companies,
        'selected_company': company,
        'services': services,
        'vehicles': vehicles,
        'active_orders': active_orders,
        'recent_orders': recent_orders,
        'appointments': appointments,
        'loyalty_account': loyalty_account,
        'loyalty_target': loyalty_target,
        'reward_description': reward_description,
        'loyalty_progress': loyalty_progress,
        'customer': customer,
        'today_str': date.today().isoformat(),
        'active_tab': request.GET.get('tab', 'services'),
        'is_select_company_page': False,
    }

    return render(request, 'portal/index.html', context)


@login_required
def portal_book_appointment(request):
    """
    Processa o agendamento de um serviço pelo cliente via interface web.
    """
    if request.method != 'POST':
        return redirect('portal:home')

    company_id = request.POST.get('company_id')
    service_id = request.POST.get('service_type_id')
    vehicle_id = request.POST.get('vehicle_id')
    scheduled_date_str = request.POST.get('scheduled_date')
    scheduled_time_str = request.POST.get('scheduled_time')
    notes = request.POST.get('notes', '').strip()

    company = get_object_or_404(Company, id=company_id, status='active')
    service = get_object_or_404(ServiceType, id=service_id, company=company)

    # Obter ou criar o perfil de Customer para a empresa de forma segura
    customer = Customer.objects.filter(user=request.user, company=company).first()
    if not customer:
        customer = Customer.objects.create(
            user=request.user,
            company=company,
            name=request.user.get_full_name() or request.user.username,
            phone=request.user.phone or '11999999999',
            email=request.user.email or '',
        )

    # Obter o veículo
    vehicle = None
    if vehicle_id:
        vehicle = Vehicle.objects.filter(id=vehicle_id, customer__user=request.user).first()

    # Se não selecionou veículo existente mas preencheu placa rápida
    if not vehicle and request.POST.get('new_vehicle_plate'):
        plate = request.POST.get('new_vehicle_plate', '').strip().upper()
        brand = request.POST.get('new_vehicle_brand', '').strip() or 'Carro'
        model_name = request.POST.get('new_vehicle_model', '').strip() or 'Passeio'
        color = request.POST.get('new_vehicle_color', '').strip() or 'Não informada'
        v_type = request.POST.get('new_vehicle_type', 'sedan')

        vehicle, _ = Vehicle.objects.get_or_create(
            company=company,
            plate=plate,
            defaults={
                'customer': customer,
                'brand': brand,
                'model': model_name,
                'color': color,
                'vehicle_type': v_type,
            }
        )

    if not vehicle:
        messages.error(request, "Por favor, selecione ou cadastre um veículo para o agendamento.")
        return redirect(f"/portal/?tab=services&company_id={company.id}")

    try:
        scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        scheduled_date = date.today()

    try:
        scheduled_time = datetime.strptime(scheduled_time_str, '%H:%M').time()
    except (ValueError, TypeError):
        scheduled_time = time(10, 0)

    # Criação do agendamento
    appointment = Appointment.objects.create(
        company=company,
        customer=customer,
        vehicle=vehicle,
        service_type=service,
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
        status='pending',
        notes=notes,
    )

    messages.success(
        request,
        f"Agendamento confirmado com sucesso para {vehicle.plate} no dia {scheduled_date.strftime('%d/%m/%Y')} às {scheduled_time.strftime('%H:%M')}!"
    )
    return redirect(f"/portal/?tab=appointments&company_id={company.id}")


@login_required
def portal_add_vehicle(request):
    """
    Cadastra um novo veículo na garagem do cliente.
    """
    if request.method == 'POST':
        company = get_active_company(request)
        if not company:
            company = Company.objects.filter(status='active').first()

        plate = request.POST.get('plate', '').strip().upper()
        brand = request.POST.get('brand', '').strip()
        model_name = request.POST.get('model', '').strip()
        color = request.POST.get('color', '').strip()
        vehicle_type = request.POST.get('vehicle_type', 'sedan')
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/portal/?tab=garage'

        if not plate or not brand or not model_name:
            messages.error(request, "Preencha placa, marca e modelo do veículo.")
            return redirect(next_url)

        # Garantir Customer de forma segura
        customer = Customer.objects.filter(user=request.user, company=company).first()
        if not customer:
            customer = Customer.objects.filter(user=request.user).first()
        if not customer:
            customer = Customer.objects.create(
                user=request.user,
                company=company,
                name=request.user.get_full_name() or request.user.username,
                phone=request.user.phone or '11999999999',
                email=request.user.email or '',
            )

        # Criar ou atualizar veículo
        vehicle, created = Vehicle.objects.get_or_create(
            company=company,
            plate=plate,
            defaults={
                'customer': customer,
                'brand': brand,
                'model': model_name,
                'color': color,
                'vehicle_type': vehicle_type,
            }
        )

        if created:
            messages.success(request, f"Veículo {plate} ({brand} {model_name}) adicionado à sua Garagem!")
        else:
            messages.info(request, f"Veículo {plate} já constava no cadastro.")

        return redirect(next_url)

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/portal/?tab=garage'
    return redirect(next_url)


@login_required
def portal_delete_vehicle(request, vehicle_id):
    """
    Remove um veículo da garagem do cliente.
    """
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, customer__user=request.user)
    plate = vehicle.plate
    vehicle.delete()
    messages.info(request, f"Veículo {plate} removido da sua garagem.")
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/portal/?tab=garage'
    return redirect(next_url)


@login_required
def portal_cancel_appointment(request, appointment_id):
    """
    Permite ao cliente cancelar um agendamento pendente.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id, customer__user=request.user)
    if appointment.status in ['pending', 'confirmed']:
        appointment.status = 'cancelled'
        appointment.save()
        messages.warning(request, f"Agendamento de {appointment.scheduled_date.strftime('%d/%m/%Y')} foi cancelado.")
    else:
        messages.error(request, "Este agendamento não pode mais ser cancelado pois o serviço já foi iniciado.")

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/portal/?tab=appointments'
    return redirect(next_url)


@login_required
def portal_live_status(request):
    """
    Retorna o status em tempo real das ordens de serviço ativas e recentes do cliente,
    com suporte para polling assíncrono e detecção de transições de status no front-end.
    """
    from apps.orders.services import get_user_service_orders
    company_id = request.GET.get('company_id')
    company = None
    if company_id and str(company_id).isdigit():
        company = Company.objects.filter(id=int(company_id), status='active').first()

    orders_qs = get_user_service_orders(request.user, company=company)

    orders_data = []
    for order in orders_qs:
        photos = [
            {
                'id': p.id,
                'photo_type': p.photo_type,
                'photo_url': p.photo.url if p.photo else '',
                'created_at': p.created_at.strftime('%H:%M') if p.created_at else '',
            }
            for p in order.photos.all()
        ]

        # Mapeamento do progresso visual
        step_progress = 25
        if order.status == 'waiting':
            step_progress = 25
        elif order.status == 'in_progress':
            step_progress = 60
        elif order.status == 'completed':
            step_progress = 90
        elif order.status == 'delivered':
            step_progress = 100

        orders_data.append({
            'id': order.id,
            'company_id': order.company_id,
            'company_name': order.company.name,
            'vehicle_plate': order.vehicle.plate if order.vehicle else '---',
            'vehicle_name': f"{order.vehicle.brand} {order.vehicle.model}" if order.vehicle else 'Veículo',
            'vehicle_color': order.vehicle.color if order.vehicle else '',
            'service_name': order.service_type.name if order.service_type else 'Lavagem Completa VIP',
            'status': order.status,
            'status_display': order.get_status_display(),
            'step_progress': step_progress,
            'total_price': float(order.total_price),
            'payment_status': order.payment_status,
            'assigned_to': order.assigned_to.get_full_name() or order.assigned_to.username if order.assigned_to else 'Especialista VIP',
            'created_at': order.created_at.strftime('%d/%m/%Y %H:%M'),
            'started_at': order.started_at.strftime('%H:%M') if order.started_at else None,
            'completed_at': order.completed_at.strftime('%H:%M') if order.completed_at else None,
            'delivered_at': order.delivered_at.strftime('%H:%M') if order.delivered_at else None,
            'photos': photos,
        })

    return JsonResponse({
        'success': True,
        'timestamp': timezone.now().isoformat(),
        'orders': orders_data,
        'active_count': len([o for o in orders_data if o['status'] not in ['delivered', 'cancelled']]),
    })
