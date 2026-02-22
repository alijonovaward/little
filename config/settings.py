import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# ============================================
# ASOSIY SOZLAMALAR
# ============================================

# SECRET KEY
SECRET_KEY = "django-insecure-development-key-change-this-in-production"

# DEBUG rejimi
DEBUG = False

# Ruxsat berilgan hostlar
ALLOWED_HOSTS = ["*"]

# CSRF ishonchli domenlar
CSRF_TRUSTED_ORIGINS = [
    "http://173.212.235.216:8000",
    "http://173.212.235.216:81",
    "https://million-halal-mart-tjj5.onrender.com",
    "https://*.onrender.com",
    "https://millionmart.uz",
]

# Login redirect
LOGIN_REDIRECT_URL = "dashboard"
LOGIN_URL = "login_page"

# Domain
DOMAIN_NAME = "https://millionmart.uz"

# ============================================
# ILOVALAR
# ============================================

LOCAL_APPS = [
    "apps.product",
    'apps.merchant.apps.MerchantConfig',
    'apps.customer.apps.CustomerConfig',
]

INSTALLED_APPS = [
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "ckeditor",
    "ckeditor_uploader",
    "debug_toolbar",
    "drf_spectacular",
] + LOCAL_APPS

# ============================================
# MIDDLEWARE
# ============================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# ============================================
# URL VA WSGI
# ============================================

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# ============================================
# TEMPLATES
# ============================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "../templates", os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ============================================
# DATABASE
# ============================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'million',
        'USER': 'million',
        'PASSWORD': 'million',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# ============================================
# PASSWORD VALIDATION
# ============================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ============================================
# INTERNATIONALIZATION
# ============================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = (
    ("en", "English"),
    ("uz", "Uzbek"),
    ("ru", "Russian"),
    ("ko", "Korean"),
)

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_LANGUAGES = ("uz", "en", "ru", "ko")

# ============================================
# STATIC VA MEDIA FILES
# ============================================

STATIC_URL = "static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "../", "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "../", "staticfiles")

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# ============================================
# REST FRAMEWORK
# ============================================

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

# ============================================
# JWT SOZLAMALARI
# ============================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=180),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=180),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ============================================
# CORS SOZLAMALARI
# ============================================

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = "*"

# ============================================
# CKEDITOR
# ============================================

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    'default': {
        'config.versionCheck': False,
    },
}

# ============================================
# DRF SPECTACULAR (SWAGGER)
# ============================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'Million Mart API',
    'DESCRIPTION': 'API for Million Mart Project',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENTS': {
        'SECURITY_SCHEMES': {
            'Bearer': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'JWT Token based authentication',
            }
        }
    },
    'SECURITY': [{'Bearer': []}],
}

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
}

# ============================================
# DEBUG TOOLBAR
# ============================================

INTERNAL_IPS = [
    "127.0.0.1",
    "0.0.0.0",
]
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: True}

# ============================================
# CUSTOM USER MODEL
# ============================================

AUTH_USER_MODEL = "customer.User"

# ============================================
# TWILIO SOZLAMALARI (bo'sh qoldiring agar kerak bo'lmasa)
# ============================================

TOKEN_LIFESPAN = 10  # mins
OTP_EXPIRE_TIME = 10  # mins
TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN = ""
TWILIO_PHONE_NUMBER = ""

# ============================================
# FIREBASE
# ============================================

FCM_SERVER_KEY = ""

# ============================================
# DEFAULT SETTINGS
# ============================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
