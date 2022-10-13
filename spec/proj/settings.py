"""
Django settings for tests project.

Generated by 'django-admin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import json
from pathlib import Path
import sys, os
import proj.signal_loggers as request_logger

# Server specific variable setup
computer_name = os.getenv('COMPUTERNAME')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = os.path.join(BASE_DIR,'frontend')
STATIC_DIR = os.path.join(FRONTEND_DIR, 'static')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-*OverrideThisInSetting.Local*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',  # https://www.django-rest-framework.org/api-guide/authentication/
    'spec.apps.SpecConfig',
    'user.apps.UserConfig',

    'django_cleanup.apps.CleanupConfig', # should be placed after your apps

]

MIDDLEWARE = [
    'utils.middleware.TimeStampMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = ['http://localhost:8081', 'http://127.0.0.1:8080', 'http://127.0.0.1:8081',  'http://127.0.0.1:8000', 'http://spec-dev01:80/']
TOKEN_EXPIRED_AFTER_SECONDS = 60*60*24*365 # one year (These are for automated interfaces)
SESSION_COOKIE_AGE = 60 * 60 * 4 # four hours of web inactivity (These are for web interactions)

ROOT_URLCONF = 'proj.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [FRONTEND_DIR, TEMPLATE_DIR],
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

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'user.authentication.ExpiringTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100
}

WSGI_APPLICATION = 'proj.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'specdb',
    }
}
AUTHENTICATION_BACKENDS = [
    'proj.util.MyLDAPBackend',
    "django.contrib.auth.backends.ModelBackend",
]

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/4.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    STATIC_DIR,
]

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOG_DIR = os.path.join(Path(__file__).resolve().parent.parent, 'logs')
LOGGING = {
                "version": 1,
                "disable_existing_loggers": False,
                'formatters': {
                    'simple': {
                        'format': ' {name}:{lineno} {levelname} {asctime} : {message}',
                        'datefmt': '%Y-%m-%d %H:%M:%S',
                        'style': '{',
                    },
                },
                "handlers": {
                    'djangoInfo': {
                        'level': 'DEBUG',
                        'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
                        'filename': os.path.join(LOG_DIR, "django.log"),
                        'maxBytes': 1024*1024*10,
                        'backupCount': 10,
                        'use_gzip': True,
                        'formatter': 'simple',
                        'delay': True,
                    },
                    'appInfo': {
                        'level': 'DEBUG',
                        'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
                        'filename': os.path.join(LOG_DIR, "spec.log"),
                        'maxBytes': 1024*1024*10,
                        'backupCount': 10,
                        'use_gzip': True,
                        'formatter': 'simple',
                        'delay': True,
                    },
                    'authInfo': {
                        'level': 'DEBUG',
                        'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
                        'filename': os.path.join(LOG_DIR, "auth.log"),
                        'maxBytes': 1024*1024*10,
                        'backupCount': 10,
                        'use_gzip': True,
                        'formatter': 'simple',
                        'delay': True,
                    },
                    "console": {
                        "class": "logging.StreamHandler",
                        'formatter': 'simple',
                    },
                },
                "loggers": {
                    'django': {
                        'handlers': ['djangoInfo'],
                        'level': 'INFO',
                        'propagate': True,
                    },
                    'requests': {
                        'handlers': ['appInfo'],
                        'level': 'INFO',
                        'propagate': True,
                    },
                    'data': {
                        'handlers': ['appInfo'],
                        'level': 'INFO',
                        'propagate': True,
                    },
                    "django_auth_ldap": {
                        "handlers": ['authInfo'],
                        "level": "INFO",
                    },
                },
            }
            
SOFFICE = None
TEMP_PDF = os.path.join(MEDIA_ROOT, 'temp')

# Override default settings
try:
    from .settings_local import *
except ImportError: #pragma nocover
    pass

from deepmerge import always_merger
try:
    if LOGGING_OVERRIDES:
        always_merger.merge(LOGGING, LOGGING_OVERRIDES)
except: #pragma nocover
    pass

request_logger.log_all_requests()