from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

CORS_ALLOW_ALL_ORIGINS = True   # only safe in dev

# Emails printed to console instead of sent
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'