from config.settings.base import *
import os
from decouple import config

# Production settings
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['*']  # Yoki config('ALLOWED_HOSTS', default='*').split(',')

# Security settings
SECURE_SSL_REDIRECT = False  # Agar SSL bo'lmasa
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = False  # SSL bo'lmasa False
CSRF_COOKIE_SECURE = False  # SSL bo'lmasa False

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USERNAME'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOSTNAME', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Static va Media fayllar
STATIC_ROOT = '/home/little/staticfiles/'
MEDIA_ROOT = '/home/little/mediafiles/'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# CSRF va CORS

CSRF_TRUSTED_ORIGINS = [
    'http://173.212.235.216:81',
]
CORS_ALLOW_ALL_ORIGINS = True  # Yoki kerakli domenlarni qo'shing