from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.saas_core.decorators import tenant_required, require_plan_feature
from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount, LoyaltyEvent

from apps.services.models import ServiceType

@tenant_required
@require_plan_feature('loyalty')
def loyalty_dashboard(request):
    program, _ = LoyaltyProgram.objects.get_or_create(company=request.company)
    accounts = LoyaltyAccount.objects.filter(company=request.company).select_related('customer').order_by('-points_balance')
    recent_events = LoyaltyEvent.objects.filter(company=request.company).select_related('account__customer')[:50]
    available_services = ServiceType.objects.filter(company=request.company, is_active=True).order_by('name')

    # Clientes que já atingiram os pontos necessários (ex: 100 pts)
    eligible_accounts = [acc for acc in accounts if acc.points_balance >= program.points_needed_for_reward]

    return render(request, 'loyalty/dashboard.html', {
        'program': program,
        'accounts': accounts,
        'recent_events': recent_events,
        'available_services': available_services,
        'eligible_accounts': eligible_accounts,
    })


@tenant_required
@require_plan_feature('loyalty')
def loyalty_configure(request):
    if request.method == 'POST':
        program, _ = LoyaltyProgram.objects.get_or_create(company=request.company)
        reward_type = request.POST.get('reward_type', 'service')
        reward_service_id = request.POST.get('reward_service_id')
        reward_product_name = request.POST.get('reward_product_name', '').strip()
        points_needed = request.POST.get('points_needed_for_reward', 100)
        is_active = request.POST.get('is_active') == 'on'

        program.reward_type = reward_type
        if reward_type == 'service' and reward_service_id:
            service = get_object_or_404(ServiceType, id=reward_service_id, company=request.company)
            program.reward_service = service
            program.reward_description = f"{service.name} (Grátis)"
            program.reward_product_name = ''
        elif reward_type == 'product' and reward_product_name:
            program.reward_service = None
            program.reward_product_name = reward_product_name
            program.reward_description = reward_product_name
        elif reward_service_id:
            service = get_object_or_404(ServiceType, id=reward_service_id, company=request.company)
            program.reward_service = service
            program.reward_description = f"{service.name} (Grátis)"
        elif reward_product_name:
            program.reward_product_name = reward_product_name
            program.reward_description = reward_product_name

        try:
            program.points_needed_for_reward = int(points_needed)
        except ValueError:
            pass

        program.is_active = is_active
        program.save()
        messages.success(request, f'🎉 Configuração do Clube Fidelidade atualizada! Alvo: {program.points_needed_for_reward} pontos • Prêmio: "{program.reward_name}".')
        return redirect('loyalty:dashboard')

    return redirect('loyalty:dashboard')


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
        description=f"Resgate de Recompensa: {program.reward_name if program else 'Prêmio'}"
    )

    messages.success(request, f'🎁 Recompensa "{program.reward_name}" resgatada para o cliente {account.customer.name} com sucesso!')
    return redirect('loyalty:dashboard')
