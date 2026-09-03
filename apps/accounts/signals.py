import logging
from django.contrib.auth.signals import user_logged_in, user_login_failed, user_logged_out
from django.dispatch import receiver

logger = logging.getLogger('apps.security')

def get_client_ip(request):
    """
    Recupera o IP real do cliente, considerando proxies/load balancers.
    """
    if not request:
        return 'UNKNOWN_IP'
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'UNKNOWN_IP')


@receiver(user_logged_in)
def log_user_login_success(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    company_name = getattr(user, 'company', None)
    role = getattr(user, 'role', 'unknown')
    logger.info(
        "SECURITY_EVENT [LOGIN_SUCCESS] User: %s (ID: %s, Role: %s, Company: %s) logged in successfully from IP: %s",
        user.username,
        user.id,
        role,
        company_name,
        ip
    )


@receiver(user_login_failed)
def log_user_login_failure(sender, credentials, request, **kwargs):
    ip = get_client_ip(request)
    attempted_username = credentials.get('username') or credentials.get('email') or 'N/A'
    logger.warning(
        "SECURITY_EVENT [LOGIN_FAILURE] Failed authentication attempt for username: %s from IP: %s",
        attempted_username,
        ip
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    username = user.username if user else 'Anonymous'
    logger.info(
        "SECURITY_EVENT [LOGOUT] User: %s logged out from IP: %s",
        username,
        ip
    )
