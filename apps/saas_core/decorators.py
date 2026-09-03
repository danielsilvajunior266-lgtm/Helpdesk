import logging
from functools import wraps
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages

security_logger = logging.getLogger('apps.security')

def tenant_required(view_func):
    """
    Exige que o usuário autenticado esteja explicitamente vinculado a uma empresa ativa/operacional.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        company = getattr(request, 'company', None)
        if request.user.is_superuser:
            if not company:
                from apps.saas_core.models import Company
                company = Company.objects.filter(status='active').first() or Company.objects.first()
                request.company = company
            if company:
                return view_func(request, *args, **kwargs)
            else:
                messages.warning(request, 'Nenhuma empresa cadastrada no SaaS. Crie uma empresa no painel administrativo.')
                return redirect('admin:index')

        if not company or not company.is_operational:
            security_logger.warning(
                "SECURITY_EVENT [TENANT_ACCESS_DENIED] User: %s (ID: %s, Role: %s) attempted access to tenant-restricted view '%s' without an active tenant.",
                request.user.username,
                request.user.id,
                getattr(request.user, 'role', 'unknown'),
                view_func.__name__
            )
            if request.headers.get('HX-Request') or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'error': 'tenant_inactive_or_missing', 'detail': 'Empresa inativa ou não encontrada.'}, status=403)
            messages.error(request, 'Sua conta não está vinculada a uma empresa ativa. Entre em contato com o suporte ou administrador.')
            return redirect('accounts:profile')

        return view_func(request, *args, **kwargs)
    return _wrapped_view


def require_plan_feature(feature_name: str):
    """
    Valida se o plano contratado da empresa possui a funcionalidade habilitada.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            company = getattr(request, 'company', None)
            if not company or not company.has_feature(feature_name):
                security_logger.warning(
                    "SECURITY_EVENT [PLAN_FEATURE_DENIED] User: %s (Company: %s, Plan: %s) attempted to access restricted feature '%s' in view '%s'.",
                    request.user.username if request.user.is_authenticated else 'Anonymous',
                    company.name if company else 'None',
                    company.plan.code if company and company.plan else 'None',
                    feature_name,
                    view_func.__name__
                )
                error_msg = f'A funcionalidade "{feature_name}" não está disponível no plano atual da sua empresa ({company.plan.name if company and company.plan else "Sem Plano"}). Faça o upgrade para utilizá-la.'
                
                # Resposta para requisições assíncronas HTMX ou API REST
                if request.headers.get('HX-Request'):
                    return HttpResponseForbidden(f'<div class="bg-amber-500/20 border border-amber-500/50 text-amber-200 p-4 rounded-xl text-sm font-medium">{error_msg}</div>')
                
                if 'application/json' in request.headers.get('Accept', ''):
                    return JsonResponse({'error': 'feature_not_available', 'detail': error_msg}, status=403)

                messages.warning(request, error_msg)
                return redirect('orders:kanban')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
