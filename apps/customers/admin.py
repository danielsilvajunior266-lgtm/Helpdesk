from django.contrib import admin
from apps.customers.models import Customer, Vehicle

class VehicleInline(admin.TabularInline):
    model = Vehicle
    extra = 1


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'billing_type', 'company', 'created_at')
    list_filter = ('billing_type', 'company')
    search_fields = ('name', 'phone', 'email', 'document')
    inlines = [VehicleInline]


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate', 'brand', 'model', 'color', 'vehicle_type', 'customer', 'company')
    list_filter = ('vehicle_type', 'company')
    search_fields = ('plate', 'brand', 'model', 'customer__name')
