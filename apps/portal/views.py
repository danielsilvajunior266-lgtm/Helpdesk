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
    Apresenta barra de busca em tempo real, destaque do último lava-jato visitado
    e catálogo de parceiros credenciados.
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

    if request.user.is_authenticated:
        last_order = ServiceOrder.objects.filter(
            customer__user=request.user
        ).select_related('company', 'vehicle', 'service_type').order_by('-created_at').first()

        last_appointment = Appointment.objects.filter(
            customer__user=request.user
        ).select_related('company', 'vehicle', 'service_type').order_by('-scheduled_date', '-scheduled_time').first()

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
            # Obtém ou inicializa perfil de cliente para este usuário
            customer = Customer.objects.filter(user=request.user, company=company).first()
            if not customer:
                customer = Customer.objects.filter(user=request.user).first()

            # Veículos do cliente
            vehicles = Vehicle.objects.filter(customer__user=request.user).distinct()

            # Ordens de serviço ativas no pátio e concluídas recentemente
            all_orders = ServiceOrder.objects.filter(
                customer__user=request.user
            ).select_related('company', 'vehicle', 'service_type').prefetch_related('photos').order_by('-created_at')

            active_orders = [o for o in all_orders if o.status not in ['delivered', 'cancelled']]
            recent_orders = [o for o in all_orders if o.status in ['delivered', 'completed']][:5]

            # Agendamentos do cliente
            appointments = Appointment.objects.filter(
                customer__user=request.user
            ).select_related('company', 'vehicle', 'service_type').order_by('-scheduled_date', '-scheduled_time')

            # Saldo e programa de fidelidade
            if company.has_feature('loyalty'):
                loyalty_account = LoyaltyAccount.objects.filter(
                    customer__user=request.user,
                    company=company
                ).prefetch_related(
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

    # Obter ou criar o perfil de Customer para a empresa
    customer, _ = Customer.objects.get_or_create(
        user=request.user,
        company=company,
        defaults={
            'name': request.user.get_full_name() or request.user.username,
            'phone': request.user.phone or '11999999999',
            'email': request.user.email,
        }
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
        plate = request.POST.get('plate', '').strip().upper()
        brand = request.POST.get('brand', '').strip()
        model_name = request.POST.get('model', '').strip()
        color = request.POST.get('color', '').strip()
        vehicle_type = request.POST.get('vehicle_type', 'sedan')

        if not plate or not brand or not model_name:
            messages.error(request, "Preencha placa, marca e modelo do veículo.")
            return redirect('/portal/?tab=garage')

        # Garantir Customer
        customer, _ = Customer.objects.get_or_create(
            user=request.user,
            company=company,
            defaults={
                'name': request.user.get_full_name() or request.user.username,
                'phone': request.user.phone or '11999999999',
                'email': request.user.email,
            }
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

    return redirect('/portal/?tab=garage')


@login_required
def portal_delete_vehicle(request, vehicle_id):
    """
    Remove um veículo da garagem do cliente.
    """
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, customer__user=request.user)
    plate = vehicle.plate
    vehicle.delete()
    messages.info(request, f"Veículo {plate} removido da sua garagem.")
    return redirect('/portal/?tab=garage')


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

    return redirect('/portal/?tab=appointments')
