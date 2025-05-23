# w1/w1/settings.py
from pathlib import Path
import os
import dj_database_url
# Corrected import: Csv and UndefinedValueError are imported here, config is imported once.
from decouple import config, Csv, UndefinedValueError

BASE_DIR = Path(__file__).resolve().parent.parent

# --- BEGIN SECRET_KEY Handling ---
# Define a placeholder key that will ONLY be used during build if the real key isn't found.
_DEFAULT_BUILD_SECRET_KEY = "this_is_a_temporary_insecure_key_for_django_build_only_789xyz_replace_if_you_want"

try:
    # Attempt to load the SECRET_KEY from the environment (Railway will provide this at runtime)
    SECRET_KEY = config('SECRET_KEY')
except UndefinedValueError:
    # This block is executed if SECRET_KEY is not found in the environment.
    # This is expected during the 'collectstatic' build phase on Railway.
    print("WARNING: SECRET_KEY not found in environment. Using a temporary default for build purposes.")
    print("         Ensure SECRET_KEY is properly set in your Railway environment variables for runtime.")
    SECRET_KEY = _DEFAULT_BUILD_SECRET_KEY

# Load DEBUG normally. Railway should set this to 'False' for production.
# Ensure DEBUG is defined *after* SECRET_KEY might have used its default,
# so the critical check below works correctly.
DEBUG = config('DEBUG', default=False, cast=bool)

# CRITICAL RUNTIME CHECK:
# If the application is running (not in DEBUG mode) and is still using the default build key,
# it means the actual SECRET_KEY from Railway's environment variables was not picked up.
# This is a security risk, so we prevent the app from starting.
if not DEBUG and SECRET_KEY == _DEFAULT_BUILD_SECRET_KEY:
    raise ValueError(
        "CRITICAL SECURITY ERROR: The application is running in a non-DEBUG environment "
        "but is using the default build-time SECRET_KEY. "
        "Please ensure the SECRET_KEY environment variable is correctly set in Railway."
    )
# --- END SECRET_KEY Handling ---

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize', # Para filtros como intcomma

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    'core.apps.CoreConfig',
]

SITE_ID = 1 # Required by django-allauth

OPENAI_API_KEY = config('OPENAI_API_KEY', default=None)
if not OPENAI_API_KEY:
    print("AVISO DE CONFIGURAÇÃO: A chave da API da OpenAI (OPENAI_API_KEY) não está definida no seu arquivo .env ou nas variáveis de ambiente.")

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Whitenoise should be high, but after SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware', # django-allauth middleware
]

ROOT_URLCONF = 'w1.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request', # Required by allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'w1.wsgi.application'

DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600, # Number of seconds database connections should persist for
            conn_health_checks=True, # Recommended for robust connections
            ssl_require=config('DB_SSL_REQUIRE', default=True, cast=bool) # Often True for cloud DBs
        )
    }
else:
    # Fallback to SQLite for local development if DATABASE_URL is not set
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("AVISO: DATABASE_URL não encontrada. Usando SQLite como fallback. "
          "Para produção, certifique-se de que DATABASE_URL está configurada.")


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True # Recommended to be True for time zone handling
USE_L10N = True # For locale-specific formatting (deprecated in Django 5.0, Django handles this by default with USE_I18N=True)

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"] # For local development static files
STATIC_ROOT = BASE_DIR / "staticfiles"  # For collectstatic output
# Ensure Whitenoise storage is used if you want compression and manifest features
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'core.User' # Custom user model

# Django Allauth settings
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend', # Default Django auth
    'allauth.account.auth_backends.AuthenticationBackend', # Allauth specific
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module}:{lineno:d} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO', # Set to DEBUG for more verbose output during development
            'class': 'logging.StreamHandler',
            'formatter': 'verbose', # Or 'simple'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO', # Root logger level
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'), # Control Django's verbosity
            'propagate': False, # Don't pass to root logger if handled here
        },
        'core': { # Your app's logger
            'handlers': ['console'],
            'level': 'DEBUG', # Or INFO
            'propagate': False,
        },
        # You can add loggers for other libraries if needed, e.g., 'allauth'
    },
}

# Allauth Account settings
ACCOUNT_USER_MODEL_USERNAME_FIELD = None # Using email as username
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email' # Users log in with email
ACCOUNT_EMAIL_VERIFICATION = 'none' # Or 'mandatory' or 'optional'. 'none' for simplicity now.
ACCOUNT_LOGIN_ON_SIGNUP = True # Log user in immediately after signup

LOGIN_REDIRECT_URL = '/dashboard/' # Default redirect after login
ACCOUNT_LOGOUT_REDIRECT_URL = '/' # Default redirect after logout

ACCOUNT_LOGOUT_ON_GET = True # Allows logout via GET request (consider security implications)
SOCIALACCOUNT_LOGIN_ON_GET = True # For social login convenience

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID', default='your-google-client-id'), # Provide defaults or ensure they are set
            'secret': config('GOOGLE_CLIENT_SECRET', default='your-google-client-secret'),
            'key': '' # Usually not needed unless for specific legacy reasons
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
            # 'prompt': 'select_account' # Uncomment to always force account selection
        }
    }
}

ZAPI_INSTANCE_ID = config('ZAPI_INSTANCE_ID', default=None)
ZAPI_CLIENT_TOKEN = config('ZAPI_CLIENT_TOKEN', default=None)
ZAPI_SECURITY_TOKEN = config('ZAPI_SECURITY_TOKEN', default=None)
ZAPI_BASE_URL = config('ZAPI_BASE_URL', default='https://api.z-api.io/instances')

if not ZAPI_INSTANCE_ID or not ZAPI_CLIENT_TOKEN or not ZAPI_SECURITY_TOKEN: # Added ZAPI_SECURITY_TOKEN check
    print("AVISO DE CONFIGURAÇÃO: Credenciais Z-API (ZAPI_INSTANCE_ID, ZAPI_CLIENT_TOKEN, ZAPI_SECURITY_TOKEN) não estão completamente definidas no .env ou nas variáveis de ambiente.")

# Email backend settings
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend') # Console for dev
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=25, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='webmaster@localhost')

# Ensure SITE_ID is defined if you removed it from INSTALLED_APPS by mistake for allauth
# It's already correctly placed before.

# If you use celery or other background tasks, configure them here.
# Example for Celery:
# CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
# CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')