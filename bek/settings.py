from pathlib import Path
import dj_database_url
from corsheaders.defaults import default_headers
import os
from decouple import config
import os
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-x*#e%6z(b&9w$2*2yq(koh@lj8qxpn)k_gl^bskbmi+=c6!!y!'

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TELEGRAM_ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))
DEBUG = False
# ALLOWED_HOSTS = [
#     'tezkor.kodi.uz', 'localhost', '127.0.0.1',
#     # "balanced-pipefish-settling.ngrok-free.app" # fake
# ]
ALLOWED_HOSTS = ["*"]

# CORS_ALLOWED_ORIGINS = [
#     "https://tezkor-donat-front.vercel.app",
#     "http://localhost:5173",
# ]
CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_HEADERS = list(default_headers) + [
    "X-User-ID",  # Заглавными буквами
]


CORS_ALLOW_CREDENTIALS = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'app',
    'transaction',

    'corsheaders',
    'django_celery_results'
]
CSRF_TRUSTED_ORIGINS = [
    "https://djangobasedback-production.up.railway.app",
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bek.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bek.wsgi.application'


DATABASES = {
    'default': dj_database_url.config(default=os.getenv("DATABASE_URL"))
}


AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', }
]


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

MOOGOLD_SECRET_KEY = config("MOOGOLD_SECRET_KEY")
MOOGOLD_PARTNER = config("MOOGOLD_PARTNER")

TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_ID = config("TELEGRAM_ADMIN_ID")

CELERY_BROKER_URL = os.getenv("REDIS_URL")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'



# YAML_OUTPUT_DIR = BASE_DIR / 'cdn/config/'

# STATIC_URL = '/cdn/'
# STATICFILES_DIRS = [
#     BASE_DIR / 'cdn',
# ]

# SECURE_SSL_REDIRECT = TRUE
SECURE_SSL_REDIRECT = False

SESSION_COOKIE_SECURE = True

STATIC_URL = '/cdn/'
STATIC_ROOT = '/var/www/tezkor-donat/static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
YAML_OUTPUT_DIR = os.path.join(BASE_DIR, 'yaml_exports')
