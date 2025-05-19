# w1/settings.py

from pathlib import Path
import os
from decouple import config, Csv  # Import Csv for ALLOWED_HOSTS
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Carrega ALLOWED_HOSTS do arquivo .env, default é uma lista vazia
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',

    # Django Allauth required app
    'django.contrib.sites', # <<< MAKE SURE THIS IS PRESENT

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google', # <<< Google provider

    'core.apps.CoreConfig',
]

# Add SITE_ID for django-allauth
SITE_ID = 1 # <<< ADD THIS LINE

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Add to existing settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Or your provider
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='your-email@gmail.com') # Load from .env
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='your-app-password') # Load from .env
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='your-email@gmail.com') # Load from .env


# Configurações do Allauth
AUTH_USER_MODEL = 'core.User'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'none' # For development; consider 'mandatory' for production
# ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*'] # This is handled by allauth's default form or custom forms
LOGIN_REDIRECT_URL = '/dashboard/' # Redirect after login
LOGOUT_REDIRECT_URL = '/' # Redirect after logout
SOCIALACCOUNT_LOGIN_ON_GET = True # This can be convenient for direct login links

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID'),
            'secret': config('GOOGLE_CLIENT_SECRET'),
            'key': '' # 'key' is usually empty for Google
            # 'FIELD_X': 'value',  # <<< REMOVE THIS EXAMPLE/PLACEHOLDER LINE
        },
        'SCOPE': [ # Information you want to request from Google
            'profile',
            'email',
        ],
        'AUTH_PARAMS': { # Additional parameters for the auth request
            'access_type': 'online', # 'offline' if you need refresh tokens
        }
        # You can add more provider-specific settings here if needed
        # For example, to prompt for account selection every time:
        # 'AUTH_PARAMS': {'prompt': 'select_account'},
    }
}
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware', # <<< Allauth middleware
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
                'django.template.context_processors.request', # <<< `allauth` needs this
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'w1.wsgi.application'

# Database
DATABASE_URL = config('DATABASE_URL', default=None)
print(f"DEBUG: DATABASE_URL lida do .env é: '{DATABASE_URL}'")

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

# Password validation
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
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Recommended: If you are using your custom User model from the start and `allauth`
# and want `allauth` to handle signups exclusively via social or its own forms,
# you might not need ACCOUNT_SIGNUP_FIELDS if you customize `allauth` forms.
# However, ACCOUNT_EMAIL_REQUIRED = True and ACCOUNT_AUTHENTICATION_METHOD = 'email' are key.

# For `allauth` to work correctly, ensure your `core.User` model's email field
# is set as unique (`unique=True`). (Which it is in your provided models.py)