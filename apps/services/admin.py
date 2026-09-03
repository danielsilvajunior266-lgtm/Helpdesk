from django.contrib import admin
from apps.services.models import ServiceCategory, ServiceType

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'company')
    list_filter = ('company',)
    search_fields = ('name',)


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'default_price', 'estimated_duration_minutes', 'counts_for_loyalty', 'is_active', 'company')
    list_filter = ('category', 'is_active', 'counts_for_loyalty', 'company')
    search_fields = ('name', 'description')
