from django.contrib import admin
from apps.commissions.models import CommissionRule, EmployeeCommission

@admin.register(CommissionRule)
class CommissionRuleAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'calc_type', 'value', 'company')
    list_filter = ('calc_type', 'company')


@admin.register(EmployeeCommission)
class EmployeeCommissionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'order', 'amount', 'status', 'paid_at', 'company')
    list_filter = ('status', 'company')
    search_fields = ('employee__first_name', 'employee__email', 'order__id')
