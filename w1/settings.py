from pathlib import Path
import os
from decouple import config, Csv # Import Csv for ALLOWED_HOSTS
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent# Ajustado para refletir que settings.py está em w1/w1/

# SECURITY WARNING: keep the secret key used in production secret!
# Carrega a SECRET_KEY do arquivo .env
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# Carrega DEBUG do arquivo .env, default é False se não encontrado
DEBUG = config('DEBUG', default=False, cast=bool)

# Carrega ALLOWED_HOSTS do arquivo .env, default é uma lista vazia
# Exemplo no .env: ALLOWED_HOSTS=127.0.0.1,localhost,.meusite.com
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Para servir estáticos com WhiteNoise em desenvolvimento
    'django.contrib.staticfiles',

    # Apps de terceiros
    'django.contrib.sites', # Necessário para django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google', # Provedor Google para login social
    
    # Seus apps
    'core.apps.CoreConfig', # Use a forma completa para carregar a configuração do app (incluindo signals)
]

SITE_ID = 1 # Necessário para django-allauth e django.contrib.sites

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # WhiteNoise deve vir depois de SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware', # Middleware do django-allauth
]

ROOT_URLCONF = 'w1.urls' # Aponta para o arquivo urls.py principal do projeto (w1/w1/urls.py)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Adicione o diretório de templates do seu app 'core' se ele existir
        # e um diretório de templates globais se você tiver um.
        'DIRS': [BASE_DIR / 'core' / 'templates'], # Procura templates em w1/core/templates/
        'APP_DIRS': True, # Permite que o Django procure templates dentro dos diretórios 'templates' de cada app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request', # Necessário para allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'w1.wsgi.application' # Aponta para o arquivo wsgi.py (w1/w1/wsgi.py)


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Configuração padrão para SQLite (usado como fallback se DATABASE_URL não estiver definida no .env)
DATABASES = {
    'default': { # Fallback para SQLite se DATABASE_URL não estiver no .env
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3', # Agora BASE_DIR / 'db.sqlite3' apontará para D:\hackaton\w1\w1\db.sqlite3
    }
}

DATABASE_URL = config('DATABASE_URL', default=None)
print(f"DEBUG: DATABASE_URL lida do .env é: '{DATABASE_URL}'") # <--- ADICIONE ESTA LINHA PARA DEBUG

if DATABASE_URL:
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=config('DB_SSL_REQUIRE', default=False, cast=bool)
    )
else:
    print("AVISO: DATABASE_URL não encontrada no .env. Usando SQLite como fallback.")



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = '/static/'
# Diretório onde o Django vai procurar por arquivos estáticos adicionais (além dos de cada app)
STATICFILES_DIRS = [
    BASE_DIR / "static", # Aponta para a pasta 'static' na raiz do projeto (w1/static/)
]
# Diretório onde `collectstatic` vai copiar todos os arquivos estáticos para deploy
STATIC_ROOT = BASE_DIR / "staticfiles"
# Para servir arquivos estáticos com WhiteNoise de forma eficiente em produção
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Media files (arquivos enviados pelos usuários, como PDFs)
# URL base para servir arquivos de mídia
MEDIA_URL = '/media/'
# Diretório no sistema de arquivos onde os arquivos de mídia serão armazenados
MEDIA_ROOT = BASE_DIR / 'mediafiles' # Cria uma pasta 'mediafiles' na raiz do projeto (w1/mediafiles/)


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Modelo de Usuário Customizado
AUTH_USER_MODEL = 'core.User' # Aponta para o seu modelo User em core/models.py

# Configurações do Allauth
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Não exige verificação de e-mail
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {

            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
}}