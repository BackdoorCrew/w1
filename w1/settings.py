# w1/w1/settings.py
from pathlib import Path
import os
import sys # Required for sys.argv
from decouple import config, UndefinedValueError, Csv # Ensure Csv is imported if you use it directly, though config handles it
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Build Process Check ---
# Helper to determine if we are in a build context (e.g., collectstatic, CI build)
# Railway might set CI=true or specific RAILWAY_... variables during build.
# Add any Railway-specific build indicators here if known.
IS_BUILD_PROCESS = (
    'collectstatic' in sys.argv or
    os.environ.get('CI') == 'true' or # Common CI environment variable
    # Add other build indicators if applicable, e.g.:
    # os.environ.get('RAILWAY_IS_BUILD_INSTANCE') == 'true' (hypothetical)
    False # Placeholder to allow leading 'or'
)
if IS_BUILD_PROCESS:
    print("INFO: settings.py: IS_BUILD_PROCESS detected as True.")
else:
    print("INFO: settings.py: IS_BUILD_PROCESS detected as False (runtime).")

# --- SECRET_KEY Configuration ---
_SECRET_KEY_DEFAULT_FOR_BUILD = 'django-insecure-this-is-a-dummy-key-for-builds-only-@-+eok%uv3$540-p!5g-abcdef'
try:
    SECRET_KEY = config('SECRET_KEY')
    print("INFO: settings.py: SECRET_KEY loaded from environment.")
except UndefinedValueError:
    if IS_BUILD_PROCESS:
        print("WARNING: settings.py: SECRET_KEY env var not found. Using DUMMY key for BUILD.")
        SECRET_KEY = _SECRET_KEY_DEFAULT_FOR_BUILD
    else:
        # This will now be the primary error if SECRET_KEY is missing at runtime.
        print("ERROR: settings.py: SECRET_KEY not found at runtime.")
        raise UndefinedValueError('CRITICAL: SECRET_KEY not found in environment. Declare it as an environment variable for runtime.')

# --- DEBUG Configuration ---
# DEBUG="True" in your Railway env will be cast to True by python-decouple.
# DEBUG="False" or if the var is missing (and default is False) will result in False.
DEBUG = config('DEBUG', default=False, cast=bool)
print(f"INFO: settings.py: DEBUG configured to: {DEBUG}")

# --- ALLOWED_HOSTS Configuration ---
# Your Railway env: ALLOWED_HOSTS="127.0.0.1,localhost,w1-production-873f.up.railway.app"
# config() with Csv caster will handle this.
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())
print(f"INFO: settings.py: ALLOWED_HOSTS: {ALLOWED_HOSTS}")


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # For development with Whitenoise
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    'core.apps.CoreConfig',
]

SITE_ID = 1 # Required by django-allauth

# --- OpenAI API Key ---
_OPENAI_API_KEY_BUILD_DEFAULT = None # Or some dummy string if needed by code during build
try:
    OPENAI_API_KEY = config('OPENAI_API_KEY')
    print("INFO: settings.py: OPENAI_API_KEY loaded.")
except UndefinedValueError:
    if IS_BUILD_PROCESS:
        print("WARNING: settings.py: OPENAI_API_KEY env var not found. Setting to default for BUILD.")
        OPENAI_API_KEY = _OPENAI_API_KEY_BUILD_DEFAULT
    elif DEBUG: # If it's runtime, but we are in DEBUG mode (local dev)
        print("WARNING: settings.py: OPENAI_API_KEY not defined in DEBUG mode. AI features may be limited.")
        OPENAI_API_KEY = None
    else: # Runtime, not DEBUG, and key is missing
        print("ERROR: settings.py: OPENAI_API_KEY not found for production runtime. AI features might fail.")
        # Option 1: Raise error if critical
        # raise UndefinedValueError('CRITICAL: OPENAI_API_KEY not found in environment for production runtime.')
        # Option 2: Set to None and let the application handle it gracefully
        OPENAI_API_KEY = None
if not OPENAI_API_KEY and not IS_BUILD_PROCESS and not DEBUG:
     print("WARNING: settings.py: OPENAI_API_KEY is not set in production runtime.")


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
                'django.template.context_processors.request', # Required by allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'w1.wsgi.application'

# --- Database Configuration ---
try:
    DATABASE_URL_FROM_ENV = config('DATABASE_URL')
    print(f"INFO: settings.py: DATABASE_URL found in environment.")
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL_FROM_ENV,
            conn_max_age=600,
            conn_health_checks=True,
            # For Railway's managed Postgres, ssl_require is often handled by the connection string.
            # If you face SSL issues, you might need to explicitly set it.
            # ssl_require=config('DB_SSL_REQUIRE', default=True, cast=bool)
        )
    }
except UndefinedValueError:
    if IS_BUILD_PROCESS:
        print("WARNING: settings.py: DATABASE_URL env var not found. Using DUMMY SQLite for BUILD.")
        DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    elif DEBUG: # Local development fallback if DATABASE_URL is not in .env
        print("WARNING: settings.py: DATABASE_URL not found. Using local db.sqlite3 for DEBUG mode.")
        DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
    else: # Runtime, not DEBUG, and DATABASE_URL is missing
        print("ERROR: settings.py: DATABASE_URL not found at runtime.")
        raise UndefinedValueError('CRITICAL: DATABASE_URL not found in environment. Declare it for runtime.')

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
USE_L10N = True # Django 5.0 default behavior when USE_I18N is True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles' # Ensure this directory is writable by the app if you upload files

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'core.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth Account settings
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'none' # Change to 'mandatory' for production if desired
ACCOUNT_LOGIN_ON_SIGNUP = True

LOGIN_REDIRECT_URL = '/dashboard/' # Or use a name: 'dashboard'
ACCOUNT_LOGOUT_REDIRECT_URL = '/' # Or use a name: 'index'
ACCOUNT_LOGOUT_ON_GET = True
SOCIALACCOUNT_LOGIN_ON_GET = True

# --- Social Account Providers Configuration ---
_GOOGLE_CLIENT_ID_BUILD = 'dummy-google-client-id-for-build'
_GOOGLE_CLIENT_SECRET_BUILD = 'dummy-google-client-secret-for-build'

try:
    _google_client_id = config('GOOGLE_CLIENT_ID')
except UndefinedValueError:
    if IS_BUILD_PROCESS:
        print("WARNING: settings.py: GOOGLE_CLIENT_ID env var not found. Using DUMMY value for BUILD.")
        _google_client_id = _GOOGLE_CLIENT_ID_BUILD
    else:
        print("ERROR: settings.py: GOOGLE_CLIENT_ID not found at runtime.")
        raise UndefinedValueError('CRITICAL: GOOGLE_CLIENT_ID not found. Declare it for runtime.')

try:
    _google_client_secret = config('GOOGLE_CLIENT_SECRET')
except UndefinedValueError:
    if IS_BUILD_PROCESS:
        print("WARNING: settings.py: GOOGLE_CLIENT_SECRET env var not found. Using DUMMY value for BUILD.")
        _google_client_secret = _GOOGLE_CLIENT_SECRET_BUILD
    else:
        print("ERROR: settings.py: GOOGLE_CLIENT_SECRET not found at runtime.")
        raise UndefinedValueError('CRITICAL: GOOGLE_CLIENT_SECRET not found. Declare it for runtime.')

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': _google_client_id,
            'secret': _google_client_secret,
            'key': '' # Usually not needed
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'}
    }
}

# --- ZAPI Configuration ---
# Applying similar robust loading for ZAPI credentials
_ZAPI_BUILD_DEFAULT = "dummy_zapi_for_build"
try:
    ZAPI_INSTANCE_ID = config('ZAPI_INSTANCE_ID')
except UndefinedValueError:
    if IS_BUILD_PROCESS: ZAPI_INSTANCE_ID = _ZAPI_BUILD_DEFAULT
    else: raise UndefinedValueError('ZAPI_INSTANCE_ID not found for runtime.')

try:
    ZAPI_CLIENT_TOKEN = config('ZAPI_CLIENT_TOKEN')
except UndefinedValueError:
    if IS_BUILD_PROCESS: ZAPI_CLIENT_TOKEN = _ZAPI_BUILD_DEFAULT
    else: raise UndefinedValueError('ZAPI_CLIENT_TOKEN not found for runtime.')

try:
    ZAPI_SECURITY_TOKEN = config('ZAPI_SECURITY_TOKEN')
except UndefinedValueError:
    if IS_BUILD_PROCESS: ZAPI_SECURITY_TOKEN = _ZAPI_BUILD_DEFAULT
    else: raise UndefinedValueError('ZAPI_SECURITY_TOKEN not found for runtime.')

ZAPI_BASE_URL = config('ZAPI_BASE_URL', default='https://api.z-api.io/instances')

if not all([
    ZAPI_INSTANCE_ID != _ZAPI_BUILD_DEFAULT if IS_BUILD_PROCESS else ZAPI_INSTANCE_ID,
    ZAPI_CLIENT_TOKEN != _ZAPI_BUILD_DEFAULT if IS_BUILD_PROCESS else ZAPI_CLIENT_TOKEN,
    ZAPI_SECURITY_TOKEN != _ZAPI_BUILD_DEFAULT if IS_BUILD_PROCESS else ZAPI_SECURITY_TOKEN
]) and not IS_BUILD_PROCESS: # Only warn loudly at runtime if not dummy
    print("WARNING: settings.py: One or more ZAPI credentials (ID, Client Token, Security Token) are missing or using build defaults at runtime.")


# --- Email Configuration ---
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=25, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='webmaster@localhost')


# --- Security Settings (from your "working" example, good practice) ---
# In production (not DEBUG), these should typically be True.
# python-decouple will cast "True"/"False" strings from env vars if you set them there.
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=not DEBUG, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=not DEBUG, cast=bool)
SECURE_PROXY_SSL_HEADER = config('SECURE_PROXY_SSL_HEADER', default='HTTP_X_FORWARDED_PROTO,https').split(',') # Read as tuple
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=not DEBUG, cast=bool)

# HSTS settings - be cautious with these, especially SECURE_HSTS_PRELOAD
# Start with small HSTS_SECONDS values in production if enabling for the first time.
# Defaulting to 0 if DEBUG is True (or not set, meaning development) is safer.
_default_hsts_seconds = 0 if DEBUG else 3600 # 1 hour for starters, increase once confirmed
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=_default_hsts_seconds, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=not DEBUG, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=not DEBUG, cast=bool)

if not DEBUG:
    print(f"INFO: settings.py: Security headers configured for production: "
          f"CSRF_COOKIE_SECURE={CSRF_COOKIE_SECURE}, SESSION_COOKIE_SECURE={SESSION_COOKIE_SECURE}, "
          f"SECURE_SSL_REDIRECT={SECURE_SSL_REDIRECT}, SECURE_HSTS_SECONDS={SECURE_HSTS_SECONDS}")

# --- Logging Configuration (adapted from your "working" example) ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}', 'style': '{'},
        'simple': {'format': '[{asctime}] {levelname} {message}', 'style': '{', 'datefmt': '%Y-%m-%d %H:%M:%S'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'} # Using 'simple' from working example
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO' # Default root level
    },
    'loggers': {
        'django': { # Django's own logs
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'), # Control Django's verbosity via env var
            'propagate': False, # Don't pass to root logger if handled here
        },
        'core': { # Your app's logger
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO', # More verbose for your app in DEBUG mode
            'propagate': False,
        },
        # Add other app loggers here if needed
    },
}

# If in DEBUG mode, set root and Django loggers to DEBUG for more verbosity
if DEBUG:
    LOGGING['root']['level'] = 'DEBUG'
    LOGGING['loggers']['django']['level'] = 'DEBUG'
    print("INFO: settings.py: DEBUG mode enabled, setting verbose logging.")