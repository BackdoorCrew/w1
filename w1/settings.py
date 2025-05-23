# w1/w1/settings.py
from pathlib import Path
import os
import dj_database_url
# We'll still use decouple for other settings
from decouple import config, Csv, UndefinedValueError

BASE_DIR = Path(__file__).resolve().parent.parent

# --- BEGIN SECRET_KEY & DEBUG Handling (using os.environ.get directly) ---
_DEFAULT_BUILD_SECRET_KEY = "this_is_a_temporary_insecure_key_for_django_build_only_direct_os_get_v2"

# Print statements to help debug what os.environ sees at runtime.
# Check your Railway logs for these print outputs.
print(f"SETTINGS.PY: Raw OS Env DEBUG: '{os.environ.get('DEBUG')}'")
print(f"SETTINGS.PY: Raw OS Env SECRET_KEY is set: {bool(os.environ.get('SECRET_KEY'))}")
if os.environ.get('SECRET_KEY'):
    print(f"SETTINGS.PY: Raw OS Env SECRET_KEY starts with: '{os.environ.get('SECRET_KEY')[:5]}'")


# Read SECRET_KEY directly from environment
SECRET_KEY_FROM_ENV = os.environ.get('SECRET_KEY')
if SECRET_KEY_FROM_ENV:
    SECRET_KEY = SECRET_KEY_FROM_ENV
    print("SETTINGS.PY: SECRET_KEY loaded directly from os.environ.")
else:
    # This block is for build time (e.g., collectstatic) or if env var is truly missing at runtime
    print("WARNING: SETTINGS.PY: SECRET_KEY not found via os.environ.get. Using build-time default. THIS IS UNEXPECTED AT RUNTIME.")
    SECRET_KEY = _DEFAULT_BUILD_SECRET_KEY

# Read DEBUG directly from environment and cast manually
DEBUG_FROM_ENV_STR = os.environ.get('DEBUG') # Get the string value, or None if not set
if DEBUG_FROM_ENV_STR is not None:
    print(f"SETTINGS.PY: DEBUG string from os.environ: '{DEBUG_FROM_ENV_STR}'")
    # Common boolean true values
    DEBUG_BOOL_TRUES = ['true', 'yes', 'on', '1']
    if DEBUG_FROM_ENV_STR.strip().lower() in DEBUG_BOOL_TRUES:
        DEBUG = True
    else:
        DEBUG = False
else:
    # DEBUG environment variable is not set at all, default to False for safety
    print("WARNING: SETTINGS.PY: DEBUG environment variable not set. Defaulting DEBUG to False.")
    DEBUG = False

print(f"SETTINGS.PY: Final DEBUG value: {DEBUG}")
print(f"SETTINGS.PY: Final SECRET_KEY is build default: {SECRET_KEY == _DEFAULT_BUILD_SECRET_KEY}")


# CRITICAL RUNTIME CHECK:
if not DEBUG and SECRET_KEY == _DEFAULT_BUILD_SECRET_KEY:
    # This check is crucial. If DEBUG is False (either explicitly set or defaulted)
    # AND SECRET_KEY is the build default (meaning it wasn't found in env by os.environ.get)
    # then it's a critical issue.
    print(f"ERROR TRIGGER: DEBUG is {DEBUG}, SECRET_KEY is using build default: {SECRET_KEY == _DEFAULT_BUILD_SECRET_KEY}")
    raise ValueError(
        "CRITICAL SECURITY ERROR (direct os.environ.get check): The application is running in a non-DEBUG environment "
        "but is using the default build-time SECRET_KEY. "
        "This usually means the SECRET_KEY and/or DEBUG environment variables from Railway are not being correctly read by the application. "
        "Check Railway logs for 'SETTINGS.PY:' print statements."
    )
# --- END SECRET_KEY & DEBUG Handling ---

# Use decouple for other variables as before
ALLOWED_HOSTS_STR = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost') # Also try direct for this
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(',')]
print(f"SETTINGS.PY: ALLOWED_HOSTS: {ALLOWED_HOSTS}")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    'core.apps.CoreConfig',
]

SITE_ID = 1

# Using config() for the rest, assuming they are less problematic or have safe defaults
OPENAI_API_KEY = config('OPENAI_API_KEY', default=None)
if not OPENAI_API_KEY:
    print("AVISO DE CONFIGURAÇÃO: A chave da API da OpenAI (OPENAI_API_KEY) não está definida.")

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
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
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'w1.wsgi.application'

# DATABASE_URL directly from os.environ, as it's critical
DATABASE_URL_FROM_ENV = os.environ.get('DATABASE_URL')
if DATABASE_URL_FROM_ENV:
    print("SETTINGS.PY: DATABASE_URL loaded directly from os.environ.")
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL_FROM_ENV, conn_max_age=600, conn_health_checks=True, ssl_require=True)
    }
else:
    print("WARNING: SETTINGS.PY: DATABASE_URL not found in os.environ. Using SQLite fallback. THIS IS UNEXPECTED FOR PRODUCTION.")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True
USE_L10N = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'core.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGGING = { # (Your existing LOGGING dict - keep as is or simplify if needed)
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module}:{lineno:d} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGIN_ON_SIGNUP = True

LOGIN_REDIRECT_URL = '/dashboard/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

ACCOUNT_LOGOUT_ON_GET = True
SOCIALACCOUNT_LOGIN_ON_GET = True

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID', default=''),
            'secret': config('GOOGLE_CLIENT_SECRET', default=''),
            'key': ''
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'}
    }
}

ZAPI_INSTANCE_ID = config('ZAPI_INSTANCE_ID', default=None)
ZAPI_CLIENT_TOKEN = config('ZAPI_CLIENT_TOKEN', default=None)
ZAPI_SECURITY_TOKEN = config('ZAPI_SECURITY_TOKEN', default=None)
ZAPI_BASE_URL = config('ZAPI_BASE_URL', default='https://api.z-api.io/instances')

if not all([ZAPI_INSTANCE_ID, ZAPI_CLIENT_TOKEN, ZAPI_SECURITY_TOKEN]):
    print("AVISO DE CONFIGURAÇÃO: Credenciais Z-API não estão completamente definidas.")

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=25, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='webmaster@localhost')