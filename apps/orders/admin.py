from django.contrib import admin
from apps.orders.models import ServiceOrder, OrderPhoto

class OrderPhotoInline(admin.TabularInline):
    model = OrderPhoto
    extra = 1


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle', 'customer', 'service_type', 'final_price', 'status', 'billing_status', 'created_at', 'company')
    list_filter = ('status', 'billing_status', 'payment_method', 'company')
    search_fields = ('vehicle__plate', 'customer__name', 'id')
    inlines = [OrderPhotoInline]


@admin.register(OrderPhoto)
class OrderPhotoAdmin(admin.ModelAdmin):
    list_display = ('order', 'stage', 'caption', 'created_at', 'company')
    list_filter = ('stage', 'company')
