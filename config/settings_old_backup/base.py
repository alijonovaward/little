import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import config
from django.core.exceptions import ImproperlyConfigured
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes", "t", "y", "on")

def get_env_value(env_variable, default=None):
    try:
        return config(env_variable)
    except Exception:
        if default is not None:
            return default
        # Build jarayonida (Render) yoki DEBUG=True bo'lganda (Local dev) xato bermasligi uchun
        if config("DEBUG", default=True, cast=str_to_bool) or config("RENDER", default=False, cast=str_to_bool):
            return ""
        error_msg = "Set the {} environment variable".format(env_variable)
        raise ImproperlyConfigured(error_msg)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_value("SECRET_KEY", default="django-insecure-development-key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False, cast=str_to_bool)

# ALLOWED_HOSTS = [get_env_value("ALLOWED_HOSTS")]
ALLOWED_HOSTS = [
    "*"
]

CSRF_TRUSTED_ORIGINS = [
    "http://173.212.235.216:8000"
]

LOGIN_REDIRECT_URL = "dashboard"

# Application definition
LOCAL_APPS = [
    "apps.product",
    'apps.merchant.apps.MerchantConfig',
    'apps.customer.apps.CustomerConfig',
]
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, "static"),
# ]
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

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Добавь эту строку здесь!
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    'default': {
        'config.versionCheck': False,
    },
}

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

CSRF_TRUSTED_ORIGINS = [
    "https://million-halal-mart-tjj5.onrender.com", # Render domeningiz
    "https://*.onrender.com",                      # Hamma render domenlar uchun
    "https://millionmart.uz",                      # Agar shaxsiy domeningiz bo'lsa
]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = "*"

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    "0.0.0.0",
    # ...
]
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: True}
# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}




# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

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
# MEDIA_URL = "/media/"
# MEDIA_ROOT = os.path.join(BASE_DIR, "../", "media/")
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
from django.urls import reverse_lazy

LOGIN_URL = reverse_lazy("login_page")
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

if RENDER_EXTERNAL_HOSTNAME:
    # Render'dagi haqiqiy yo'l
    MEDIA_ROOT = '/opt/render/project/src/mediafiles'
else:
    # Local kompyuter uchun yo'l
    MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

MEDIA_URL = '/media/'

STATIC_URL = "static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "../", "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "../", "staticfiles")
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TOKEN_LIFESPAN = 10  # mins
OTP_EXPIRE_TIME = 10  # mins
TWILIO_ACCOUNT_SID = get_env_value("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = get_env_value("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = get_env_value("TWILIO_PHONE_NUMBER")
FCM_SERVER_KEY = get_env_value("FCM_SERVER_KEY")

DOMAIN_NAME = "https://millionmart.uz"

# DATABASES = {
#     'default': dj_database_url.config(
#         default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
#         conn_max_age=600,
#         ssl_require=False  # Для локальной базы SSL не нужен
#     )
# }

# # Если мы на сервере (DATABASE_URL есть), включаем SSL (обязательно для Render)
# if os.environ.get('DATABASE_URL'):
#     DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'
#     DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False, # Session authni o'chirib qo'ygan ma'qul, chalkashmaslik uchun
    'JSON_EDITOR': True,
}
AUTH_USER_MODEL = "customer.User"
DATABASE_URL = config('DATABASE_URL', default=None)

DB_NAME = config("DB_NAME", default=None)
DB_USERNAME = config("DB_USERNAME", default=None)
DB_PASSWORD = config("DB_PASSWORD", default=None)
DB_HOSTNAME = config("DB_HOSTNAME", default=None)
DB_PORT = config("DB_PORT", default=None)

DB_SSLMODE = config("DB_SSLMODE", default=None)
DB_CHANNEL_BINDING = config("DB_CHANNEL_BINDING", default=None)

if DATABASE_URL:
    # Render yoki Neon.tech uchun DATABASE_URL (whitespace'larni tozalaymiz)
    DATABASE_URL = DATABASE_URL.strip()
    
    # AGAR foydalanuvchi adashib terminal komandasini (psql '...') tashlab yuborgan bo'lsa:
    if DATABASE_URL.startswith("psql "):
        # 'psql ' qismini olib tashlaymiz
        DATABASE_URL = DATABASE_URL.replace("psql ", "", 1).strip()
    
    # Qo'shtirnoqlar (' yoki ") bo'lsa tozalaymiz
    DATABASE_URL = DATABASE_URL.strip("'").strip('"')

    try:
        DATABASES = {
            'default': dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=600,
            )
        }
        # SSL rejimini Render va Neon uchun majburiy qilamiz
        if DATABASES['default'].get('ENGINE') == 'django.db.backends.postgresql':
            DATABASES['default'].setdefault('OPTIONS', {})['sslmode'] = 'require'
    except Exception as e:
        # Xatolikni aniqroq ko'rsatamiz
        error_msg = f"DATABASE_URL ni o'qib bo'lmadi: {e}. URL: {DATABASE_URL[:20]}..."
        raise ImproperlyConfigured(error_msg)
elif all([DB_NAME, DB_USERNAME, DB_PASSWORD, DB_HOSTNAME]):
    # Если DATABASE_URL НЕ найден, но есть DB_* переменные (например, docker-compose)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": DB_NAME,
            "USER": DB_USERNAME,
            "PASSWORD": DB_PASSWORD,
            "HOST": DB_HOSTNAME,
            "PORT": DB_PORT or "5432",
        }
    }
else:
    # Если DATABASE_URL НЕ найден (локальная разработка), используем SQLite
    # Чтобы проект не выдавал ошибку ENGINE
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',  # PostgreSQL driver
            'NAME': 'million',  # DB nomi
            'USER': 'username',  # DB foydalanuvchi
            'PASSWORD': '1111',  # foydalanuvchi paroli
            'HOST': 'localhost',  # yoki server IP / docker service name
            'PORT': '5432',  # default port
        }
    }

# Optional Postgres connection hardening/tuning.
# You can also set these via DATABASE_URL query params, e.g.
#   ?sslmode=require&channel_binding=require
if DATABASES.get("default", {}).get("ENGINE") == "django.db.backends.postgresql":
    options = DATABASES["default"].setdefault("OPTIONS", {})
    if DB_SSLMODE:
        options.setdefault("sslmode", DB_SSLMODE)
    if DB_CHANNEL_BINDING:
        options["channel_binding"] = DB_CHANNEL_BINDING

SIMPLE_JWT = {
    # Время жизни Access Token (теперь 180 дней)
    'ACCESS_TOKEN_LIFETIME': timedelta(days=180),

    # Время жизни Refresh Token (лучше сделать его таким же или больше)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=180),

    # Остальные стандартные настройки
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
