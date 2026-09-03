from django.contrib import admin
from apps.finance.models import CashCategory, CashEntry

@admin.register(CashCategory)
class CashCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'company')
    list_filter = ('category_type', 'company')
    search_fields = ('name',)


@admin.register(CashEntry)
class CashEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_date', 'description', 'entry_type', 'amount', 'payment_method', 'category', 'company')
    list_filter = ('entry_type', 'payment_method', 'entry_date', 'company')
    search_fields = ('description',)
