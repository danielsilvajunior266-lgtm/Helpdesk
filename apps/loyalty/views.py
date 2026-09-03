from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.saas_core.decorators import tenant_required, require_plan_feature
from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount, LoyaltyEvent

@tenant_required
@require_plan_feature('loyalty')
def loyalty_dashboard(request):
    program, _ = LoyaltyProgram.objects.get_or_create(company=request.company)
    accounts = LoyaltyAccount.objects.filter(company=request.company).select_related('customer')
    recent_events = LoyaltyEvent.objects.filter(company=request.company).select_related('account__customer')[:50]

    return render(request, 'loyalty/dashboard.html', {
        'program': program,
        'accounts': accounts,
        'recent_events': recent_events,
    })


@tenant_required
@require_plan_feature('loyalty')
def redeem_reward(request, account_id):
    account = get_object_or_404(LoyaltyAccount, id=account_id, company=request.company)
    program = LoyaltyProgram.objects.filter(company=request.company).first()
    needed = program.points_needed_for_reward if program else 100

    if account.points_balance < needed:
        messages.error(request, f'Saldo insuficiente ({account.points_balance} pts). Necessário: {needed} pts.')
        return redirect('loyalty:dashboard')

    account.points_balance -= needed
    account.total_rewards_redeemed += 1
    account.save()

    LoyaltyEvent.objects.create(
        company=request.company,
        account=account,
        event_type='redeemed',
        points=-needed,
        description=f"Resgate de Recompensa: {program.reward_description if program else 'Prêmio'}"
    )

    messages.success(request, f'Recompensa resgatada para {account.customer.name} com sucesso!')
    return redirect('loyalty:dashboard')
