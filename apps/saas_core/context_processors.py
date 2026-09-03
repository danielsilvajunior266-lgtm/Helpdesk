def tenant_context(request):
    """
    Injeta o contexto do Tenant atual e suas flags de recursos nos templates Django.
    """
    company = getattr(request, 'company', None)
    features = {}
    if company and company.plan:
        plan = company.plan
        features = {
            'has_mobile_booking': company.has_feature('mobile_booking'),
            'has_loyalty': company.has_feature('loyalty'),
            'has_monthly_billing': company.has_feature('monthly_billing'),
            'has_inspections': company.has_feature('inspections'),
            'has_commissions': company.has_feature('commissions'),
            'has_push_notifications': company.has_feature('push_notifications'),
            'has_custom_reports': company.has_feature('custom_reports'),
        }

    return {
        'current_company': company,
        'tenant_features': features,
    }
