from django.contrib import admin
from apps.employees.models import RegisteredEmployee, SalaryPayment, DailyHelper, DailyWork

@admin.register(RegisteredEmployee)
class RegisteredEmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'role_title', 'company', 'monthly_salary', 'payment_day', 'phone', 'is_active', 'hire_date')
    list_filter = ('company', 'is_active', 'role_title')
    search_fields = ('name', 'cpf', 'phone', 'company__name')


@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'company', 'reference_month', 'total_paid', 'payment_date', 'payment_method', 'status')
    list_filter = ('company', 'reference_month', 'payment_method', 'status')
    search_fields = ('employee__name', 'reference_month', 'company__name')


@admin.register(DailyHelper)
class DailyHelperAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'phone', 'pix_key')
    list_filter = ('company',)
    search_fields = ('name', 'phone', 'company__name')


@admin.register(DailyWork)
class DailyWorkAdmin(admin.ModelAdmin):
    list_display = ('helper', 'company', 'work_date', 'shift', 'daily_rate', 'status', 'payment_method', 'paid_at')
    list_filter = ('company', 'status', 'shift', 'work_date')
    search_fields = ('helper__name', 'activity_description', 'company__name')
