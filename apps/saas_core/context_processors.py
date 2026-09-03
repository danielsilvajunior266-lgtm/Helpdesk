def tenant_context(request):
    """
    Injeta o contexto do Tenant atual, suas flags de recursos e as notificações operacionais
    (agendamentos recebidos, avisos de licença/plano e frotas) nos templates Django.
    """
    company = getattr(request, 'company', None)
    features = {}
    notifications = []

    if company and company.plan:
        features = {
            'has_mobile_booking': company.has_feature('mobile_booking'),
            'has_loyalty': company.has_feature('loyalty'),
            'has_monthly_billing': company.has_feature('monthly_billing'),
            'has_inspections': company.has_feature('inspections'),
            'has_commissions': company.has_feature('commissions'),
            'has_push_notifications': company.has_feature('push_notifications'),
            'has_custom_reports': company.has_feature('custom_reports'),
        }

        # 1. Alertas de Agendamentos Pendentes (Web & App)
        from apps.appointments.models import Appointment
        from django.urls import reverse
        from django.utils import timezone

        pending_appointments = Appointment.objects.filter(
            company=company,
            status='pending'
        ).select_related('customer', 'vehicle', 'service_type').order_by('-scheduled_date', '-scheduled_time')[:5]

        for app in pending_appointments:
            is_vip_text = " 👑 (VIP)" if getattr(app.customer, 'is_vip', False) else ""
            notifications.append({
                'id': f"app_{app.id}",
                'type': 'appointment',
                'title': 'Novo Agendamento Recebido',
                'message': f"{app.customer.name}{is_vip_text} agendou {app.service_type.name} ({app.vehicle.plate}) para {app.scheduled_date.strftime('%d/%m/%Y')} às {app.scheduled_time}.",
                'time': app.created_at,
                'link': reverse('appointments:list'),
                'icon': 'calendar-plus',
                'color': 'cyan',
                'badge': 'Agendamento'
            })

        # 2. Alertas de Licença do Plano / Assinatura
        subscription = company.subscriptions.order_by('-due_date').first() if hasattr(company, 'subscriptions') else None
        if subscription:
            days_left = (subscription.due_date - timezone.now().date()).days
            if days_left <= 7 and subscription.status != 'paid':
                notifications.append({
                    'id': f"sub_{subscription.id}",
                    'type': 'license_warning',
                    'title': 'Vencimento da Licença do Plano',
                    'message': f"Atenção: A mensalidade do plano {company.plan.name} vence em {days_left} dia(s). Mantenha sua assinatura em dia.",
                    'time': timezone.now(),
                    'link': '#',
                    'icon': 'alert-triangle',
                    'color': 'gold',
                    'badge': 'Licença'
                })
            elif subscription.status == 'paid':
                notifications.append({
                    'id': f"sub_{subscription.id}_ok",
                    'type': 'license_ok',
                    'title': 'Licença do Plano Ativa',
                    'message': f"Sua licença do plano {company.plan.name} está ativa e regularizada.",
                    'time': subscription.paid_at or timezone.now(),
                    'link': '#',
                    'icon': 'shield-check',
                    'color': 'emerald',
                    'badge': 'Plano Ativo'
                })
        else:
            notifications.append({
                'id': f"plan_{company.id}",
                'type': 'plan_active',
                'title': 'Licença do Plano Ativa',
                'message': f"Sua empresa está operando com o plano {company.plan.name}.",
                'time': company.created_at,
                'link': '#',
                'icon': 'shield-check',
                'color': 'emerald',
                'badge': 'Plano Ativo'
            })

        # 3. Alertas de Faturamento de Frotas em Aberto
        if features.get('has_monthly_billing'):
            from apps.billing.models import MonthlyInvoice
            open_invoices = MonthlyInvoice.objects.filter(company=company, status='open').count()
            if open_invoices > 0:
                notifications.append({
                    'id': f"inv_{company.id}",
                    'type': 'billing_open',
                    'title': 'Faturas Mensais em Aberto',
                    'message': f"Você possui {open_invoices} fatura(s) de frotistas aguardando fechamento ou pagamento.",
                    'time': timezone.now(),
                    'link': reverse('billing:list'),
                    'icon': 'receipt',
                    'color': 'bronze',
                    'badge': 'Frotas'
                })

    unread_count = len([n for n in notifications if n['type'] in ['appointment', 'license_warning', 'billing_open']])

    return {
        'current_company': company,
        'tenant_features': features,
        'notifications': notifications,
        'unread_notifications_count': unread_count,
    }
