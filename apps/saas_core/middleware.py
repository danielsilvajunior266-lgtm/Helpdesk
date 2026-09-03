from apps.saas_core.models import Company

class TenantMiddleware:
    """
    Middleware responsável por interceptar toda requisição HTTP e injetar
    a instância da Company corrente em `request.company`.
    Prioridades:
    1. Se o usuário estiver autenticado, usa request.user.company.
    2. Caso contrário (ex: rotas públicas da API Mobile), tenta ler o header 'X-Company-ID'.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        company = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            company = getattr(request.user, 'company', None)

        if not company:
            # Tenta buscar por sessão ou header X-Company-ID
            session_company_id = getattr(request, 'session', {}).get('selected_company_id') if hasattr(request, 'session') else None
            company_id = session_company_id or request.headers.get('X-Company-ID')
            if company_id and str(company_id).isdigit():
                try:
                    company = Company.objects.select_related('plan').get(id=int(company_id))
                except Company.DoesNotExist:
                    company = None

        if not company and (request.path.startswith('/portal/') or (hasattr(request, 'user') and request.user.is_authenticated and getattr(request.user, 'role', None) == 'customer')):
            company = Company.objects.filter(status='active').select_related('plan').first()

        request.company = company
        return self.get_response(request)
