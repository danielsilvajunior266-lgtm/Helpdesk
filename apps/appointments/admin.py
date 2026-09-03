from django.contrib import admin
from apps.appointments.models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'vehicle', 'service_type', 'scheduled_date', 'scheduled_time', 'status', 'company')
    list_filter = ('status', 'scheduled_date', 'company')
    search_fields = ('customer__name', 'vehicle__plate')
