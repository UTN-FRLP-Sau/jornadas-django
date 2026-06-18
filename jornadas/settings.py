from pathlib import Path
from decouple import config
from datetime import date

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', cast=lambda v: [s.strip() for s in v.split(',')])


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'charlas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'jornadas.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'charlas' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'charlas.context_processors.es_token_user',
            ],
        },
    },
]

WSGI_APPLICATION = 'jornadas.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
}

LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/dashboard/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER')

# Sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

SITE_URL = config('SITE_URL', default='http://localhost:8000')


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'reminders_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / f'reminders_{date.today().strftime("%Y-%m-%d")}.log',
            'formatter': 'reminders',
        },
    },
    'formatters': {
        'reminders': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'loggers': {
        'send_reminders': {
            'handlers': ['reminders_file'],
            'level': 'INFO',
        },
    },
}
