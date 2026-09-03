from django.contrib import admin
from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount, LoyaltyEvent

@admin.register(LoyaltyProgram)
class LoyaltyProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_needed_for_reward', 'reward_description', 'points_per_service', 'is_active', 'company')
    list_filter = ('is_active', 'company')


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = ('customer', 'points_balance', 'total_points_earned', 'total_rewards_redeemed', 'company')
    list_filter = ('company',)
    search_fields = ('customer__name',)


@admin.register(LoyaltyEvent)
class LoyaltyEventAdmin(admin.ModelAdmin):
    list_display = ('account', 'event_type', 'points', 'description', 'created_at', 'company')
    list_filter = ('event_type', 'company')
    search_fields = ('account__customer__name', 'description')
