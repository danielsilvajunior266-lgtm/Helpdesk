from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.saas_core.decorators import tenant_required
from apps.appointments.models import Appointment
from apps.appointments.services import convert_appointment_to_order

@tenant_required
def appointment_list(request):
    appointments = Appointment.objects.filter(company=request.company).select_related(
        'customer', 'vehicle', 'service_type', 'preferred_employee', 'order'
    )
    return render(request, 'appointments/list.html', {'appointments': appointments})


@tenant_required
def check_in_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, company=request.company)
    order = convert_appointment_to_order(appointment)
    messages.success(request, f"Entrada confirmada! Serviço nº {order.id} iniciado e adicionado ao Pátio.")
    return redirect('orders:kanban')


@tenant_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, company=request.company)
    appointment.status = 'cancelled'
    appointment.save()
    messages.info(request, "Agendamento cancelado.")
    return redirect('appointments:list')
