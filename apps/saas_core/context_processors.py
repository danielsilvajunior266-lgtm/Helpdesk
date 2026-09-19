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
            'has_employees': company.plan.code == 'premium' or company.has_feature('commissions') or company.has_feature('employees'),
            'has_push_notifications': company.has_feature('push_notifications'),
            'has_custom_reports': company.has_feature('custom_reports'),
        }

        # 1. Alertas de Agendamentos Pendentes (Web & App)
        from apps.appointments.models import Appointment
        from django.urls import reverse
        from django.utils import timezone
        from datetime import date, timedelta

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

        # 3. Alertas de Faturamento de Frotas e Cobrança Mensal por Cliente Frotista
        if features.get('has_monthly_billing'):
            from apps.billing.models import MonthlyInvoice
            from apps.customers.models import Customer
            from apps.orders.models import ServiceOrder

            # 3.1. Faturas já geradas em aberto aguardando liquidação
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
                    'color': 'gold',
                    'badge': 'Frotas'
                })

            # 3.2. Notificação mensal por cliente frotista com serviços acumulados prontos para cobrança
            fleet_customers = Customer.objects.filter(company=company, billing_type='monthly')
            for fc in fleet_customers:
                pending_orders = ServiceOrder.objects.filter(
                    company=company,
                    customer=fc,
                    status__in=['completed', 'delivered'],
                    billing_status='PENDING'
                ).select_related('vehicle', 'service_type').order_by('-completed_at', '-created_at')

                if pending_orders.exists():
                    orders_count = pending_orders.count()
                    total_val = sum(o.final_price for o in pending_orders)
                    plates = list(dict.fromkeys(o.vehicle.plate for o in pending_orders if o.vehicle))[:3]
                    plates_text = f" ({', '.join(plates)})" if plates else ""

                    notifications.append({
                        'id': f"fleet_due_{company.id}_{fc.id}",
                        'type': 'fleet_billing_due',
                        'title': f"Cobrança Mensal • {fc.name}",
                        'message': f"Lembrete de Cobrança: O frotista {fc.name} possui {orders_count} serviço(s) acumulados{plates_text} no valor total de R$ {total_val:.2f}. Gere a fatura para cobrar o cliente.",
                        'time': pending_orders.first().completed_at or pending_orders.first().created_at,
                        'link': reverse('billing:list'),
                        'icon': 'truck',
                        'color': 'cyan',
                        'badge': 'Cobrança Frotista'
                    })

        # 4. Alertas de Pagamento de Salário dos Funcionários (Plano Premium - 5º dia útil)
        if features.get('has_employees'):
            today = timezone.now().date()
            # Cálculo exato do 5º dia útil no Brasil (Segunda a Sexta, sem contar Sábados e Domingos)
            curr = date(today.year, today.month, 1)
            b_days = 0
            fifth_business_day = None
            while b_days < 5:
                if curr.weekday() < 5:  # 0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex
                    b_days += 1
                    if b_days == 5:
                        fifth_business_day = curr
                        break
                curr += timedelta(days=1)

            # Verifica funcionários registrados ativos que ainda não receberam no mês de referência (mês anterior)
            from apps.employees.models import RegisteredEmployee, SalaryPayment
            if today.month == 1:
                ref_month = f"12/{today.year - 1}"
            else:
                ref_month = f"{today.month - 1:02d}/{today.year}"

            active_employees = RegisteredEmployee.objects.filter(company=company, is_active=True)
            if active_employees.exists():
                paid_emp_ids = SalaryPayment.objects.filter(
                    company=company,
                    reference_month=ref_month,
                    status='paid'
                ).values_list('employee_id', flat=True)

                unpaid_count = active_employees.exclude(id__in=paid_emp_ids).count()
                if unpaid_count > 0:
                    weekday_names = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
                    day_name = weekday_names[fifth_business_day.weekday()]
                    is_late = today > fifth_business_day
                    notifications.append({
                        'id': f"salary_alert_{company.id}_{ref_month}",
                        'type': 'salary_due' if not is_late else 'salary_late',
                        'title': 'Folha de Pagamento da Equipe' if not is_late else 'Salários da Equipe Pendentes',
                        'message': f"Lembrete: O pagamento dos funcionários ({ref_month}) deve ser realizado até o 5º dia útil ({fifth_business_day.strftime('%d/%m')} - {day_name}). {unpaid_count} colaborador(es) aguardando pagamento.",
                        'time': timezone.now(),
                        'link': reverse('employees:dashboard') + '?tab=registered',
                        'icon': 'users',
                        'color': 'gold' if not is_late else 'red',
                        'badge': '5º Dia Útil' if not is_late else 'Salário Pendente'
                    })

        # 5. Alertas do Clube de Fidelidade (Clientes que alcançaram 100 pontos e ganharam o serviço recompensa)
        if features.get('has_loyalty'):
            from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount
            program = LoyaltyProgram.objects.filter(company=company, is_active=True).first()
            if program:
                needed_pts = program.points_needed_for_reward or 100
                reward_service_title = program.reward_name

                ready_accounts = LoyaltyAccount.objects.filter(
                    company=company,
                    points_balance__gte=needed_pts
                ).select_related('customer')

                for acc in ready_accounts:
                    notifications.append({
                        'id': f"loyalty_reward_{company.id}_{acc.id}",
                        'type': 'loyalty_reward_available',
                        'title': f"🎁 Prêmio de Fidelidade • {acc.customer.name}",
                        'message': f"Parabéns! O cliente {acc.customer.name} completou {acc.points_balance} pontos e ganhou um(a) {reward_service_title}! Acesse o Clube Fidelidade para liberar o prêmio.",
                        'time': timezone.now(),
                        'link': reverse('loyalty:dashboard'),
                        'icon': 'gift',
                        'color': 'gold',
                        'badge': f"{acc.points_balance} Pontos"
                    })

    unread_count = len([n for n in notifications if n['type'] in ['appointment', 'license_warning', 'billing_open', 'fleet_billing_due', 'salary_due', 'salary_late', 'loyalty_reward_available']])

    return {
        'current_company': company,
        'tenant_features': features,
        'notifications': notifications,
        'unread_notifications_count': unread_count,
    }
