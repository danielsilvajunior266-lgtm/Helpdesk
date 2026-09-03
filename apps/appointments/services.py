from django.db import transaction
from apps.appointments.models import Appointment
from apps.orders.models import ServiceOrder

def convert_appointment_to_order(appointment: Appointment) -> ServiceOrder:
    """
    Converte um agendamento confirmado na entrada física do veículo no pátio, gerando a ServiceOrder.
    """
    with transaction.atomic():
        if appointment.order:
            return appointment.order

        order = ServiceOrder.objects.create(
            company=appointment.company,
            customer=appointment.customer,
            vehicle=appointment.vehicle,
            service_type=appointment.service_type,
            assigned_to=appointment.preferred_employee,
            price=appointment.service_type.default_price,
            final_price=appointment.service_type.default_price,
            status='waiting',
            notes=f"Origem: Agendamento Online (#{appointment.id}). Obs: {appointment.notes}"
        )

        appointment.order = order
        appointment.status = 'arrived'
        appointment.save()

        return order
