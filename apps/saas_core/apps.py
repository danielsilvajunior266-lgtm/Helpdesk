from django.apps import AppConfig
from django.db.backends.signals import connection_created

def configure_sqlite(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA journal_mode = WAL;')
        cursor.execute('PRAGMA synchronous = NORMAL;')
        cursor.execute('PRAGMA cache_size = -64000;')  # 64MB Cache
        cursor.execute('PRAGMA busy_timeout = 5000;')  # 5s Timeout

class SaasCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.saas_core'
    verbose_name = 'SaaS Multi-Tenant'

    def ready(self):
        connection_created.connect(configure_sqlite)
