"""
Django settings for director project.

Generated by 'django-admin startproject' using Django 1.9b1.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import os
import sys
import socket

# Set host and IP address
try:
    HOSTNAME = socket.gethostname()
except:
    HOSTNAME = None
try:
    IP = socket.gethostbyname(HOSTNAME)
except:
    IP = None

# Set deployment mode
if len(sys.argv) > 1 and sys.argv[1] in ('runserver', 'runsslserver'):
    MODE = 'local'
elif HOSTNAME == 'stencila-director-vagrant':
    MODE = 'vagrant'
elif HOSTNAME == 'stencila-director-prod':
    MODE = 'prod'
else:
    MODE = 'local'  # Fallback for when running "./manage.py makemigrations" etc

# Set Django settings accordingly
DEBUG = MODE == 'local'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Secrets

def secret(name):
    '''
    Get a secret from the filesystem
    '''
    return file(os.path.join(BASE_DIR, '..', '..', 'secrets', name+'.txt')).read()


# Django's secret key
if MODE in ('local',):
    SECRET_KEY = 'an-insecure-key-only-used-in-development'
else:
    SECRET_KEY = secret('director-secret-key')

# Keys for UserTokens
if MODE in ('local',):
    # Use an insecure version during development
    USER_TOKEN_01_PASSWORD, USER_TOKEN_01_SECRET = ''.join(['P']*32), ''.join(['S']*32)
else:
    USER_TOKEN_01_PASSWORD, USER_TOKEN_01_SECRET = secret('director-usertoken').split()

# Token for communication between roles
if MODE in ('local',):
    COMMS_TOKEN = 'an-insecure-token-only-used-in-development'
else:
    COMMS_TOKEN = secret('stencila-comms-token')

# AWS keys for launching session hosts, SES email and S3 storage
if MODE in ('vagrant', 'prod'):
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY = secret('aws-access-key').split()


# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.9/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    'stenci.la',
    'www.stenci.la',
    'localhost',
    '127.0.0.1'
]

# A tuple that lists people who get code error notifications.
# When DEBUG=False and a view raises an exception,
# Django will email these people with the full exception
# information.
ADMINS = (
    ('Nokome Bentley', 'nokome@stenci.la'),
)

# Email addresses
# The email address that error messages come from, such as those sent to ADMINS
SERVER_EMAIL = 'hub@stenci.la'
# Default email address to use for various automated correspondence from the
# site manager (i.e. using `send_mail`)
DEFAULT_FROM_EMAIL = 'hub@stenci.la'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django.contrib.sites',  # Required by allauth

    # Third party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # Social account providers. See
    #    http://django-allauth.readthedocs.org/en/latest/providers.html
    # When you add an item here you must:
    #   - add an entry in SOCIALACCOUNT_PROVIDERS below
    #   - register Stencila as an API client or app with the provider
    #   - add a SocialApp instance (/admin/socialaccount/socialapp/add/) adding the credentials provided by the provider
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.linkedin',
    'allauth.socialaccount.providers.orcid',
    'allauth.socialaccount.providers.twitter',

    'debug_toolbar',
    'django_crontab',
    'django_user_agents',
    'reversion',
    'django_extensions',
    'semanticuiform',
    'storages',

    # Stencila apps
    'accounts',
    'builds',
    'components',
    'snippets',
    'sessions_',
    'users',
    'visits'
]
if MODE == 'local':
    # Apps for making Django development server act more like
    # the production server
    INSTALLED_APPS += (
        'corsheaders',
    )

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Third party middleware
    'django_user_agents.middleware.UserAgentMiddleware',

    # Stencila custom middleware
    'general.authentication.AuthenticationMiddleware',
    'general.errors.ErrorMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'general', 'templates'),
            os.path.join(BASE_DIR, 'users', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # This project's custom context variables
                'general.context_processors.custom'
            ],
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

if MODE in ('local', 'vagrant'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
elif MODE in ('prod',):
    host, port, name, user, password = secret('director-postgres').split()
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'HOST': host,
            'PORT': port,
            'NAME': name,
            'USER': user,
            'PASSWORD': password,
        }
    }
else:
    raise EnvironmentError('Database not configured for MODE %s' % MODE)


# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

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


# Migrations
# Disable when testing. See:
#   http://stackoverflow.com/questions/25161425/disable-migrations-when-running-unit-tests-in-django-1-7
#   https://gist.github.com/NotSqrt/5f3c76cd15e40ef62d09
if len(sys.argv) > 1 and sys.argv[1] == 'test':

    class DisableMigrations(object):
        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            return "notmigrations"

    MIGRATION_MODULES = DisableMigrations()


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = (
    # General static files, not tied to a particular app
    os.path.join(BASE_DIR, 'general', 'static'),
    os.path.join(BASE_DIR, 'general', 'node_modules'),
)

# Uploaded files
MEDIA_URL = '/uploads/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')

# Logging
# Log entries of WARNING and ERROR to go to console and to file

LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.mkdir(LOGS_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING'
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(pathname)s %(lineno)d %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'django.log'),
            'formatter': 'verbose'
        },
    },
}

###############################################################################
# Installed apps settings

# django.contrib.sites
SITE_ID = 1

# django.contrib.auth
AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',

    # Stencila custom auth backends
    'general.authentication.BasicAuthBackend',
    'general.authentication.TokenAuthBackend',
    'general.authentication.GuestAuthBackend',
)
LOGIN_URL = '/me/signin'
LOGIN_REDIRECT_URL = '/'

# django-ses
if MODE in ('vagrant', 'prod'):
    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_SES_REGION_NAME = 'us-west-2'
    AWS_SES_REGION_ENDPOINT = 'email.us-west-2.amazonaws.com'

# django-storages
if MODE in ('vagrant', 'prod'):
    AWS_STORAGE_BUCKET_NAME = 'hub'
    DEFAULT_FILE_STORAGE = 'general.custom_storages.UploadsS3BotoStorage'
    # Static files currently not hosted on S3 but this is the setup
    # STATICFILES_STORAGE = 'general.custom_storages.StaticS3BotoStorage'

# django-allauth
#
# For a full list of configuration options see
#   http://django-allauth.readthedocs.org/en/latest/configuration.html
#
# These settings seem to be used over the usual ones described here:
#   https://docs.djangoproject.com/en/1.9/ref/settings/#std:setting-SESSION_COOKIE_AGE
ACCOUNT_SESSION_REMEMBER = True # Always remember the user
ACCOUNT_SESSION_COOKIE_AGE = 31536000 # Sessions to last up to a year 60*60*24*365
# Specifies the adapter class to use, allowing you to override certain default behaviour.
SOCIALACCOUNT_ADAPTER = 'general.allauth_adapter.SocialAccountAdapter'
# Is the user required to provide an e-mail address when signing up?
ACCOUNT_EMAIL_REQUIRED = True
# Request e-mail address from 3rd party account provider?
SOCIALACCOUNT_QUERY_EMAIL = True
# Settings for each provider
SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        # See https://github.com/pennersr/django-allauth#facebook
        # Manage the app at http://developers.facebook.com logged in as user `stencila`
        # Callback URL must be HTTP
        'SCOPE': ['email'],
        'METHOD': 'oauth2',
    },
    'github': {
        # See http://developer.github.com/v3/oauth/#scopes for list of scopes available
        # At the time of writing it was not clear if scopes are implemented in allauth for Github
        # see https://github.com/pennersr/django-allauth/issues/369
        # Manage the app at https://github.com/organizations/stencila/settings/applications/74505
        # Callback URL must be HTTP
        'SCOPE': ['user:email']
    },
    'google': {
        # Manage the app at
        #   https://code.google.com/apis/console/
        #   https://cloud.google.com/console/project/582496091484/apiui/credential
        #   https://cloud.google.com/console/project/582496091484/apiui/consent
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'}
    },
    'linkedin': {
        # Manage the app at
        #  https://www.linkedin.com/developer/apps/3129843/auth
        # logged in as a user with access rights to the app
        # The scopes are listed on the above page
        'SCOPE': ['r_fullprofile', 'r_emailaddress'],
        'PROFILE_FIELDS': [
            'id',
            'first-name',
            'last-name',
            'email-address',
            'picture-url',
            'public-profile-url'
        ]
    },
    'orcid': {
        # Manage the app at https://orcid.org/developer-tools logged in as 0000-0003-1608-7967 (Nokome Bentley)
    },
    'twitter': {
        # Manage the app at https://dev.twitter.com/apps/5640979/show logged in as user `stencila`
    },
}

# raven (for getsentry.com)
# See http://raven.readthedocs.org/en/latest/integrations/django.html
if MODE in ('vagrant', 'prod'):
    # Configure
    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)
    import raven
    RAVEN_CONFIG = {
        'dsn': secret('sentry-dsn'),
        # This seems to crash start up on vagrant
        #'release': raven.fetch_git_sha(os.path.dirname(os.path.dirname(__file__)))
    }

    # 404 reporting currently turned off
    # It is recommended that this goes at top of middleware
    # http://raven.readthedocs.org/en/latest/integrations/django.html#logging
    # MIDDLEWARE_CLASSES = ('raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware',) + MIDDLEWARE_CLASSES

    # Add Sentry to logging configuration
    LOGGING['handlers']['sentry'] = {
        'level': 'WARNING',
        'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
    }
    LOGGING['root']['handlers'].append('sentry')

# django-crontab
# Run `python manage.py crontab add` whenever CRONJOBS is modified!
CRONJOBS = [
    # Every 5 minutes, check for, and stop stale sessions
    ('*/5 * * * *', 'sessions_.models.sessions_vacuum'),
    # Every hour, update worker stats
    ('0 * * * *', 'sessions_.models.workers_update'),
]

###########################################################################################
# Localizable settings
#
# Stuff which developers might wan't to override in their own settings_local.py

# Should a stub be used so that code can be tested during development
# without a running curator and/or worker
CURATOR_STUB = False
WORKER_STUB = False

# During development should `/get/web` be served from
# ... static local development build at `/srv/stencila/store/get/web` OR
GET_LOCAL = False
# ... a locally running `stencila/web/server.js` which compiles on the fly
# (run it with `make web-devserve` in that repo)
GET_DEVSERVE = False

# During devopment include Intercom?
INTERCOM_ON = True

try:
    from local_settings import *
except ImportError:
    pass
