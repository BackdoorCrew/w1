# w1/w1/settings.py
from pathlib import Path
import os
from decouple import config, Csv
import dj_database_url
from decouple import config 
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
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

SITE_ID = 1
OPENAI_API_KEY = config('OPENAI_API_KEY', default=None)
if not OPENAI_API_KEY:
    print("AVISO DE CONFIGURAÇÃO: A chave da API da OpenAI (OPENAI_API_KEY) não está definida no seu arquivo .env.")
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

DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=config('DB_SSL_REQUIRE', default=False, cast=bool)
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("AVISO: DATABASE_URL não encontrada no .env. Usando SQLite como fallback.")

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
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module}:{lineno:d} {message}', # Added lineno for better tracing
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO', # Or DEBUG for even more
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
            'level': 'INFO',
            'propagate': False,
        },
        'core': { # Your app's logger
            'handlers': ['console'],
            'level': 'INFO', # Set to INFO or DEBUG
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

# Redirecionamento padrão após login (usado pelo allauth se não houver 'next')
# A view 'login' customizada e a view 'dashboard' tratarão a lógica de onde enviar o usuário.
LOGIN_REDIRECT_URL = '/dashboard/' # Usuários existentes vão para o dashboard com sidebar

# Redirecionamento após logout
ACCOUNT_LOGOUT_REDIRECT_URL = '/' # Redireciona para a página inicial (index) após logout

# Configuração para logout direto via GET e para pular a página intermediária do Google
ACCOUNT_LOGOUT_ON_GET = True # <<< ADICIONE/MODIFIQUE ESTA LINHA
SOCIALACCOUNT_LOGIN_ON_GET = True 

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID'),
            'secret': config('GOOGLE_CLIENT_SECRET'),
            'key': ''
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'}
        # Para forçar a seleção de conta toda vez (útil para desenvolvimento/teste com múltiplas contas Google)
        # 'AUTH_PARAMS': {'access_type': 'online', 'prompt': 'select_account'}
    }
}

ZAPI_INSTANCE_ID = config('ZAPI_INSTANCE_ID', default=None)
ZAPI_CLIENT_TOKEN = config('ZAPI_CLIENT_TOKEN', default=None)
ZAPI_BASE_URL = config('ZAPI_BASE_URL', default='https://api.z-api.io/instances')

if not ZAPI_INSTANCE_ID or not ZAPI_CLIENT_TOKEN:
    print("AVISO DE CONFIGURAÇÃO: Credenciais Z-API (ZAPI_INSTANCE_ID, ZAPI_CLIENT_TOKEN) não estão definidas no .env.")

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=25, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='webmaster@localhost')
