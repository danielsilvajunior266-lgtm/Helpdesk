from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.saas_core.decorators import tenant_required, require_plan_feature
from apps.commissions.models import EmployeeCommission, CommissionRule
from apps.commissions.services import pay_commission

@tenant_required
@require_plan_feature('commissions')
def commission_list(request):
    commissions = EmployeeCommission.objects.filter(company=request.company).select_related('employee', 'order__vehicle')
    rules = CommissionRule.objects.filter(company=request.company).select_related('service_type')
    return render(request, 'commissions/list.html', {
        'commissions': commissions,
        'rules': rules,
    })


@tenant_required
@require_plan_feature('commissions')
def commission_pay(request, commission_id):
    commission = get_object_or_404(EmployeeCommission, id=commission_id, company=request.company)
    pay_commission(commission)
    messages.success(request, f"Comissão de R$ {commission.amount} paga com sucesso para {commission.employee.get_full_name() or commission.employee.username}!")
    return redirect('commissions:list')
