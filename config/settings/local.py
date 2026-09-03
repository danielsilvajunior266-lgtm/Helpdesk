from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://192.168.1.109:8000',
]
