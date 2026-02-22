# from config.settings.base import *
# from decouple import config

# #
# # DEBUG = config("DEBUG")
# #
# # # STATIC_URL = "static/"
# # # STATIC_ROOT = os.path.join(BASE_DIR, "../", "staticfiles")
# # DATABASES = {
# #     "default": {
# #         "ENGINE": "django.db.backends.postgresql",
# #         "NAME": config("DB_NAME"),
# #         "USER": config("DB_USERNAME"),
# #         "PASSWORD": config("DB_PASSWORD"),
# #         "HOST": config("DB_HOSTNAME"),
# #         "PORT": config("DB_PORT"),
# #     }
# # }
from config.settings.base import *
from decouple import config

# =====================================================
# OLD CODE (COMMENTED, NOT REMOVED)
# =====================================================

#
# DEBUG = config("DEBUG")
#
# # STATIC_URL = "static/"
# # STATIC_ROOT = os.path.join(BASE_DIR, "../", "staticfiles")
#
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": config("DB_NAME"),
#         "USER": config("DB_USERNAME"),
#         "PASSWORD": config("DB_PASSWORD"),
#         "HOST": config("DB_HOSTNAME"),
#         "PORT": config("DB_PORT"),
#     }
# }

# =====================================================
# ADDED FOR LOCAL DEVELOPMENT (SAFE)
# =====================================================

# --- DEBUG FOR LOCAL ---
DEBUG = True

# --- ALLOWED HOSTS FOR LOCAL ---
ALLOWED_HOSTS = [
   "*"
]


# --- SIMPLE SQLITE DB FOR LOCAL (NO PROD DB TOUCH) ---
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }
