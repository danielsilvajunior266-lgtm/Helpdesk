from django.contrib import admin
from apps.billing.models import MonthlyInvoice, MonthlyInvoiceItem

class MonthlyInvoiceItemInline(admin.TabularInline):
    model = MonthlyInvoiceItem
    extra = 0
    readonly_fields = ('order', 'vehicle_plate', 'service_name', 'service_date', 'amount')


@admin.register(MonthlyInvoice)
class MonthlyInvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'reference_month', 'reference_year', 'total_amount', 'status', 'due_date', 'paid_at', 'company')
    list_filter = ('status', 'reference_year', 'reference_month', 'company')
    search_fields = ('customer__name', 'id')
    inlines = [MonthlyInvoiceItemInline]
