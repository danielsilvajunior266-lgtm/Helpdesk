from django.contrib import admin
from apps.saas_core.models import Plan, Company, Subscription

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'monthly_price', 'max_users', 'has_loyalty', 'has_monthly_billing', 'has_inspections', 'has_commissions')
    list_filter = ('code',)
    search_fields = ('name', 'code')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'document', 'plan', 'status', 'city', 'state', 'created_at')
    list_filter = ('status', 'plan', 'state')
    search_fields = ('name', 'slug', 'document', 'email')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('company', 'plan', 'amount', 'due_date', 'status', 'paid_at')
    list_filter = ('status', 'due_date')
    search_fields = ('company__name',)
