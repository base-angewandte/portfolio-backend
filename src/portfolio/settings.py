"""Django settings for portfolio project.

Generated by 'django-admin startproject' using Django 1.11.15.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/

Before deployment please see
https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/
"""

import os
import sys
from email.utils import getaddresses
from urllib.parse import urlparse

import environ
from apimapper import config as apiconfig
from hashids import Hashids

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from general.utils import get_language_lazy

env = environ.Env()
env.read_env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


PROJECT_NAME = '.'.join(__name__.split('.')[:-1])

try:
    from .secret_key import SECRET_KEY
except ImportError:
    from django.core.management.utils import get_random_secret_key

    with open(os.path.join(BASE_DIR, PROJECT_NAME, 'secret_key.py'), 'w+') as f:
        SECRET_KEY = get_random_secret_key()
        f.write("SECRET_KEY = '%s'\n" % SECRET_KEY)

try:
    from .hashids_salt import HASHIDS_SALT
except ImportError:
    from django.core.management.utils import get_random_secret_key

    with open(os.path.join(BASE_DIR, PROJECT_NAME, 'hashids_salt.py'), 'w+') as f:
        HASHIDS_SALT = get_random_secret_key()
        f.write("HASHIDS_SALT = '%s'\n" % HASHIDS_SALT)

HASHIDS = Hashids(salt=HASHIDS_SALT, min_length=16)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)

# Detect if executed under test
TESTING = any(
    test in sys.argv
    for test in (
        'test',
        'csslint',
        'jenkins',
        'jslint',
        'jtest',
        'lettuce',
        'pep8',
        'pyflakes',
        'pylint',
        'sloccount',
    )
)

DOCKER = env.bool('DOCKER', default=True)

SITE_URL = env.str('SITE_URL')

FORCE_SCRIPT_NAME = env.str('FORCE_SCRIPT_NAME', default='/portfolio')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[urlparse(SITE_URL).hostname])

BEHIND_PROXY = env.bool('BEHIND_PROXY', default=True)

DJANGO_ADMIN_PATH = env.str('DJANGO_ADMIN_PATH', default='admin')

DJANGO_ADMINS = env('DJANGO_ADMINS', default=None)

if DJANGO_ADMINS:
    ADMINS = getaddresses([DJANGO_ADMINS])
    MANAGERS = ADMINS

SUPERUSERS = env.tuple('DJANGO_SUPERUSERS', default=())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'django_filters',
    'django_extensions',
    'django_cas_ng',
    'django_rq',
    'django_cleanup.apps.CleanupConfig',
    'corsheaders',
    # Project apps
    'general',
    'core',
    'api',
    'media_server',
    'docs',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django_cas_ng.backends.CASBackend',
]

LOGIN_URL = reverse_lazy('cas_ng_login')
LOGOUT_URL = reverse_lazy('cas_ng_logout')

CAS_SERVER_URL = env.str('CAS_SERVER', default=f'{SITE_URL}cas/')
CAS_LOGIN_MSG = None
CAS_LOGGED_MSG = None
CAS_RENEW = False
CAS_LOGOUT_COMPLETELY = True
CAS_RETRY_LOGIN = True
CAS_VERSION = env.str('CAS_VERSION', default='3')
CAS_APPLY_ATTRIBUTES_TO_USER = True
CAS_REDIRECT_URL = env.str('CAS_REDIRECT_URL', default=FORCE_SCRIPT_NAME or '/')
CAS_CHECK_NEXT = env.bool('CAS_CHECK_NEXT', default=True)
CAS_VERIFY_CERTIFICATE = env.bool('CAS_VERIFY_CERTIFICATE', default=True)
CAS_RENAME_ATTRIBUTES = env.dict('CAS_RENAME_ATTRIBUTES', default={})

""" Email settings """
SERVER_EMAIL = 'error@%s' % urlparse(SITE_URL).hostname

EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', default='')
EMAIL_HOST = env.str('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=25)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_USE_LOCALTIME = env.bool('EMAIL_USE_LOCALTIME', default=True)

EMAIL_SUBJECT_PREFIX = '{} '.format(env.str('EMAIL_SUBJECT_PREFIX', default='[Portfolio]').strip())
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = os.path.join(BASE_DIR, '..', 'tmp', 'emails')

    if not os.path.exists(EMAIL_FILE_PATH):
        os.makedirs(EMAIL_FILE_PATH)

""" Https settings """
if SITE_URL.startswith('https'):
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000

X_FRAME_OPTIONS = 'DENY'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if BEHIND_PROXY:
    MIDDLEWARE += [
        'general.middleware.SetRemoteAddrFromForwardedFor',
    ]
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ROOT_URLCONF = f'{PROJECT_NAME}.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
        },
    },
]

WSGI_APPLICATION = f'{PROJECT_NAME}.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('POSTGRES_DB', f'django_{PROJECT_NAME}'),
        'USER': os.environ.get('POSTGRES_USER', f'django_{PROJECT_NAME}'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', f'password_{PROJECT_NAME}'),
        'HOST': f'{PROJECT_NAME}-postgres' if DOCKER else 'localhost',
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en'
TIME_ZONE = 'Europe/Vienna'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = (
    ('de', _('German')),
    ('en', _('English')),
)

LANGUAGES_DICT = dict(LANGUAGES)

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATICFILES_DIRS = ('{}{}'.format(os.path.normpath(os.path.join(BASE_DIR, 'static')), os.sep),)
STATIC_URL = '{}/s/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
STATIC_ROOT = '{}{}'.format(os.path.normpath(os.path.join(BASE_DIR, 'assets', 'static')), os.sep)

MEDIA_URL = '{}/m/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
MEDIA_ROOT = '{}{}'.format(os.path.normpath(os.path.join(BASE_DIR, 'assets', 'media')), os.sep)

PROTECTED_MEDIA_URL = '{}/p/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
PROTECTED_MEDIA_ROOT = '{}{}'.format(os.path.normpath(os.path.join(BASE_DIR, 'assets', 'protected')), os.sep)
PROTECTED_MEDIA_LOCATION = '{}/internal/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
PROTECTED_MEDIA_SERVER = 'nginx' if not DEBUG else 'django'

FILE_UPLOAD_PERMISSIONS = 0o644

""" Logging """
LOG_DIR = os.path.join(BASE_DIR, '..', 'logs')

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'},
        'simple': {'format': '%(levelname)s %(message)s'},
        'simple_with_time': {'format': '%(levelname)s %(asctime)s %(message)s'},
    },
    'handlers': {
        'null': {'level': 'DEBUG', 'class': 'logging.NullHandler'},
        'console': {'level': 'DEBUG', 'class': 'logging.StreamHandler', 'formatter': 'simple'},
        'file': {
            'level': 'DEBUG',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'application.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 1000,
            'use_gzip': True,
            'delay': True,
            'formatter': 'verbose',
        },
        'mail_admins': {'level': 'ERROR', 'class': 'django.utils.log.AdminEmailHandler'},
        'stream_to_console': {'level': 'DEBUG', 'class': 'logging.StreamHandler'},
        'rq_console': {'level': 'DEBUG', 'class': 'logging.StreamHandler', 'formatter': 'simple_with_time'},
        'rq_file': {
            'level': 'DEBUG',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'rq.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 1000,
            'use_gzip': True,
            'delay': True,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {'handlers': ['console', 'file', 'mail_admins'], 'propagate': True, 'level': 'INFO'},
        'django': {'handlers': ['console', 'file', 'mail_admins'], 'propagate': True, 'level': 'INFO'},
        'django.request': {'handlers': ['console', 'file', 'mail_admins'], 'level': 'ERROR', 'propagate': True},
        'rq.worker': {'handlers': ['rq_console', 'rq_file', 'mail_admins'], 'level': 'DEBUG', 'propagate': False},
    },
}

""" Cache settings """
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://{}:6379/0'.format(f'{PROJECT_NAME}-redis' if DOCKER else 'localhost'),
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}

RQ_QUEUES = {
    'default': {'USE_REDIS_CACHE': 'default', 'DEFAULT_TIMEOUT': 500},
    'video': {'USE_REDIS_CACHE': 'default', 'DEFAULT_TIMEOUT': 7200},
    'high': {'USE_REDIS_CACHE': 'default', 'DEFAULT_TIMEOUT': 14400},
}

if DEBUG or TESTING:
    for queueConfig in iter(RQ_QUEUES.values()):
        queueConfig['ASYNC'] = False

RQ_EXCEPTION_HANDLERS = ['general.rq.handlers.exception_handler']

RQ_FAILURE_TTL = 2628288  # approx. 3 month


""" Session settings """
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_NAME = f'sessionid_{PROJECT_NAME}'
SESSION_COOKIE_DOMAIN = env.str('SESSION_COOKIE_DOMAIN', default=None)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CSRF_COOKIE_NAME = f'csrftoken_{PROJECT_NAME}'
CSRF_COOKIE_DOMAIN = env.str('CSRF_COOKIE_DOMAIN', default=None)
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

CORS_ALLOW_CREDENTIALS = env.bool('CORS_ALLOW_CREDENTIALS', default=False)
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=False)
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_URLS_REGEX = r'^/(api|autosuggest)/.*$'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework.authentication.SessionAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    # 'DEFAULT_THROTTLE_CLASSES': (
    #     'rest_framework.throttling.UserRateThrottle'
    # ),
    # 'DEFAULT_THROTTLE_RATES': {
    #     'user': '100/minute'
    # },
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ORDERING_PARAM': 'sort',
    'EXCEPTION_HANDLER': 'api.portfolio_exception_handler',
}

SWAGGER_SETTINGS = {'SECURITY_DEFINITIONS': {}}

OPEN_API_VERSION = env.str('OPEN_API_VERSION', default='2.0')
ACTIVE_SCHEMAS = env.list(
    'ACTIVE_SCHEMAS',
    default=[
        'architecture',
        'audio',
        'award',
        'concert',
        'conference',
        'conference_contribution',
        'design',
        'document',
        'event',
        'exhibition',
        'fellowship_visiting_affiliation',
        'festival',
        'image',
        'performance',
        'research_project',
        'sculpture',
        'software',
        'video',
    ],
)

if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(
        MIDDLEWARE.index('django.contrib.sessions.middleware.SessionMiddleware'),
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )
    INTERNAL_IPS = ('127.0.0.1',)

SKOSMOS_API = 'https://voc.uni-ak.ac.at/skosmos/rest/v1/'
TAX_ID = 'potax'
TAX_GRAPH = 'http://base.uni-ak.ac.at/portfolio/taxonomy/'
VOC_ID = 'povoc'
VOC_GRAPH = 'http://base.uni-ak.ac.at/portfolio/vocabulary/'
LANGUAGES_VOCID = 'languages'

EN_LABELS_TITLE_CASE = env.bool('EN_LABELS_TITLE_CASE', default=True)

ANGEWANDTE_API_KEY = env.str('ANGEWANDTE_API_KEY', default='')
PRIMO_API_URL = env.str('PRIMO_API_URL', default='https://apigw.obvsg.at/primo/v1/search')
PRIMO_API_KEY = env.str('PRIMO_API_KEY', default='')
GEONAMES_USER = env.str('GEONAMES_USER', default=None)
PELIAS_API_KEY = env.str('PELIAS_API_KEY', default=None)
PELIAS_API_URL = env.str('PELIAS_API_URL', default='https://api.geocode.earth/v1')
PELIAS_SOURCE_NAME = env.str('PELIAS_SOURCE_NAME', default='geocode.earth')

ACCEPT_LANGUAGE_HEADER = {'Accept-Language': get_language_lazy()}

# Autosuggest
SOURCES = {
    'ANGEWANDTE_PERSON': {
        apiconfig.URL: f'{SITE_URL}autosuggest/v1/persons/',
        apiconfig.QUERY_FIELD: 'q',
        apiconfig.PAYLOAD: None,
        apiconfig.TIMEOUT: 10,
        apiconfig.HEADER: {'Authorization': f'Bearer {ANGEWANDTE_API_KEY}'},
    },
    'GND_PERSON': {
        apiconfig.URL: 'https://lobid.org/gnd/search',
        apiconfig.QUERY_FIELD: 'q',
        apiconfig.PAYLOAD: {'format': 'json:suggest', 'filter': 'type:Person'},
        apiconfig.HEADER: ACCEPT_LANGUAGE_HEADER,
    },
    'GND_INSTITUTION': {
        apiconfig.URL: 'https://lobid.org/gnd/search',
        apiconfig.QUERY_FIELD: 'q',
        apiconfig.PAYLOAD: {'format': 'json:suggest', 'filter': 'type:CorporateBody'},
    },
    'VIAF_PERSON': {
        apiconfig.URL: 'http://www.viaf.org/viaf/AutoSuggest',
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.PAYLOAD: None,
    },
    'VIAF_INSTITUTION': {
        apiconfig.URL: 'http://www.viaf.org/viaf/AutoSuggest',
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.PAYLOAD: None,
    },
    'GND_PLACE': {
        apiconfig.URL: 'https://lobid.org/gnd/search',
        apiconfig.QUERY_FIELD: 'q',
        apiconfig.PAYLOAD: {'format': 'json:suggest', 'filter': 'type:PlaceOrGeographicName'},
    },
    'VIAF_PLACE': {
        apiconfig.URL: 'http://www.viaf.org/viaf/AutoSuggest',
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.PAYLOAD: None,
    },
    'GEONAMES_PLACE': {
        apiconfig.URL: 'http://api.geonames.org/search',
        apiconfig.QUERY_FIELD: 'q',
        apiconfig.PAYLOAD: {'maxRows': 10, 'username': GEONAMES_USER, 'type': 'json'},
    },
    'BASE_KEYWORDS': {
        apiconfig.URL: f'{SKOSMOS_API}basekw/search',
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'lang': get_language_lazy(),
            'group': 'http://base.uni-ak.ac.at/recherche/keywords/collection_base',
            'fields': 'prefLabel',
        },
    },
    'VOC_KEYWORDS': {
        apiconfig.URL: f'{SKOSMOS_API}disciplines/search',
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        # NOTE: SKOSMOS API does not return anything if the query string is simply a wildward
        apiconfig.PAYLOAD: {'lang': get_language_lazy(), 'fields': 'prefLabel'},
    },
    'VOC_ROLES': {
        apiconfig.URL: f'{SKOSMOS_API}povoc/search',
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'lang': get_language_lazy(),
            'parent': 'http://base.uni-ak.ac.at/portfolio/vocabulary/role',
            'unique': True,
            'fields': 'prefLabel',
        },
    },
    'VOC_FORMATS': {
        apiconfig.URL: f'{SKOSMOS_API}povoc/search',
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'lang': get_language_lazy(),
            'parent': 'http://base.uni-ak.ac.at/portfolio/vocabulary/format_type',
            'unique': True,
            'fields': 'prefLabel',
        },
    },
    'VOC_MATERIALS': {
        apiconfig.URL: f'{SKOSMOS_API}povoc/search',
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'lang': get_language_lazy(),
            'parent': 'http://base.uni-ak.ac.at/portfolio/vocabulary/material_type',
            'unique': True,
            'fields': 'prefLabel',
        },
    },
    'VOC_LANGUAGES': {
        apiconfig.URL: f'{SKOSMOS_API}languages/search',
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {'lang': get_language_lazy(), 'unique': True, 'fields': 'prefLabel'},
    },
    'VOC_TEXTTYPES': {
        apiconfig.URL: f'{SKOSMOS_API}povoc/search',
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'lang': get_language_lazy(),
            'parent': 'http://base.uni-ak.ac.at/portfolio/vocabulary/text_type',
            'unique': True,
            'fields': 'prefLabel',
        },
    },
    'PELIAS': {
        apiconfig.URL: f'{PELIAS_API_URL}/autocomplete',
        apiconfig.QUERY_FIELD: 'text',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'api_key': PELIAS_API_KEY,
            'focus.point.lat': env.float('PELIAS_FOCUS_POINT_LAT', default=48.208126),
            'focus.point.lon': env.float('PELIAS_FOCUS_POINT_LON', default=16.382464),
            'lang': get_language_lazy(),
            'layers': (
                'address,venue,neighbourhood,locality,borough,localadmin,county,macrocounty,region,macroregion,country,'
                'coarse,postalcode'
            ),
        },
    },
    'PRIMO_IMPORT': {
        apiconfig.URL: PRIMO_API_URL,
        apiconfig.QUERY_FIELD: 'q',
        apiconfig.PAYLOAD: {'vid': 'OBV', 'scope': 'OBV_Gesamt', 'limit': 100},
        apiconfig.TIMEOUT: 10,
        apiconfig.HEADER: {'apikey': PRIMO_API_KEY},
    },
}

ANGEWANDTE_MAPPING = {
    'source': 'uuid',
    'label': 'label',
}
GND_MAPPING = {
    'source': 'id',  # common_schema: GND schema
    'label': 'label',
}

VIAF_CONTRIBUTORS_MAPPING = {
    'label': 'displayForm',
}
VIAF_PLACES_MAPPING = {
    'label': 'toponymName',
}
GEONAMES_MAPPING = {
    'label': 'toponymName',
}
BASE_KEYWORDS_MAPPING = {
    'source': 'uri',
    'label': 'prefLabels',
}

VOC_MAPPING = {
    'source': 'uri',
    'label': 'prefLabel',
    'prefLabels': 'prefLabels',
}
PELIAS_MAPPING = {
    'source': ('properties', 'gid'),
    'label': ('properties', 'label'),
    'house_number': ('properties', 'housenumber'),
    'street': ('properties', 'street'),
    'postcode': ('properties', 'postalcode'),
    'locality': ('properties', 'locality'),
    'region': ('properties', 'region'),
    'country': ('properties', 'country'),
    'geometry': ('geometry',),
}

PRIMO_MAPPING = {
    'source': ('pnx', 'search', 'lsr33'),
    'label': ('pnx', 'search', 'title'),
    'isbn': ('pnx', 'search', 'isbn'),
    'description': ('pnx', 'search', 'description'),
    'author': ('pnx', 'display', 'creator'),
    'pages': ('pnx', 'display', 'format'),
    'creationdate': ('pnx', 'display', 'creationdate'),
    'type': ('pnx', 'display', 'type'),
    'lad24': ('pnx', 'addata', 'lad24'),
    'lds16': ('pnx', 'display', 'lds16'),
    'language': ('pnx', 'display', 'language'),
    'subject': ('pnx', 'display', 'subject'),
    'contributors': ('pnx', 'display', 'contributor'),
    'ispartof': ('pnx', 'display', 'ispartof'),
}


RESPONSE_MAPS = {
    'ANGEWANDTE_PERSON': {
        apiconfig.DIRECT: ANGEWANDTE_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"Angewandte"'}},
    },
    'GND_PERSON': {apiconfig.DIRECT: GND_MAPPING, apiconfig.RULES: {'source_name': {apiconfig.RULE: '"GND"'}}},
    'GND_INSTITUTION': {apiconfig.DIRECT: GND_MAPPING, apiconfig.RULES: {'source_name': {apiconfig.RULE: '"GND"'}}},
    'VIAF_PERSON': {
        apiconfig.RESULT: 'result',
        apiconfig.FILTER: {'nametype': 'personal'},
        apiconfig.DIRECT: VIAF_CONTRIBUTORS_MAPPING,
        apiconfig.RULES: {
            'source_name': {apiconfig.RULE: '"VIAF"'},
            'source': {apiconfig.RULE: '"http://www.viaf.org/viaf/{p1}"', apiconfig.FIELDS: {'p1': 'viafid'}},
        },
    },
    'VIAF_INSTITUTION': {
        apiconfig.RESULT: 'result',
        apiconfig.FILTER: {'nametype': 'corporate'},
        apiconfig.DIRECT: VIAF_CONTRIBUTORS_MAPPING,
        apiconfig.RULES: {
            'source_name': {apiconfig.RULE: '"VIAF"'},
            'source': {apiconfig.RULE: '"http://www.viaf.org/viaf/{p1}"', apiconfig.FIELDS: {'p1': 'viafid'}},
        },
    },
    'GND_PLACE': {apiconfig.DIRECT: GND_MAPPING, apiconfig.RULES: {'source_name': {apiconfig.RULE: '"GND"'}}},
    'VIAF_PLACE': {
        apiconfig.RESULT: 'result',
        apiconfig.FILTER: {'nametype': 'geographic'},
        apiconfig.DIRECT: VIAF_PLACES_MAPPING,
        apiconfig.RULES: {
            'source_name': {apiconfig.RULE: '"VIAF"'},
            'source': {apiconfig.RULE: '"http://www.viaf.org/viaf/{p1}"', apiconfig.FIELDS: {'p1': 'viafid'}},
        },
    },
    'GEONAMES_PLACE': {
        apiconfig.RESULT: 'geonames',
        apiconfig.DIRECT: GEONAMES_MAPPING,
        apiconfig.RULES: {
            'source_name': {apiconfig.RULE: '"GEONAMES"'},
            'source': {
                apiconfig.RULE: '"http://api.geonames.org/get?geonameId={p1}"',
                apiconfig.FIELDS: {'p1': 'geonameId'},
            },
        },
    },
    'BASE_KEYWORDS': {
        apiconfig.RESULT: 'results',
        apiconfig.DIRECT: BASE_KEYWORDS_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"base"'}},
    },
    'VOC_KEYWORDS': {
        apiconfig.RESULT: 'results',
        apiconfig.DIRECT: VOC_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"voc"'}},
    },
    'VOC_ROLES': {apiconfig.RESULT: 'results', apiconfig.DIRECT: VOC_MAPPING},
    'VOC_FORMATS': {
        apiconfig.RESULT: 'results',
        apiconfig.DIRECT: VOC_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"portfolio"'}},
    },
    'VOC_MATERIALS': {
        apiconfig.RESULT: 'results',
        apiconfig.DIRECT: VOC_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"portfolio"'}},
    },
    'VOC_LANGUAGES': {
        apiconfig.RESULT: 'results',
        apiconfig.DIRECT: VOC_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"voc"'}},
    },
    'VOC_TEXTTYPES': {apiconfig.RESULT: 'results', apiconfig.DIRECT: VOC_MAPPING},
    'PELIAS': {
        apiconfig.RESULT: 'features',
        apiconfig.DIRECT: PELIAS_MAPPING,
        apiconfig.RULES: {
            'source_name': {apiconfig.RULE: f'"{PELIAS_SOURCE_NAME}"'},  # noqa: B907 - this has to be in double quotes
            'source': {
                apiconfig.RULE: f'"{PELIAS_API_URL}/place?ids={{p1}}"',
                apiconfig.FIELDS: {'p1': ('properties', 'gid')},
            },
        },
    },
    'PRIMO_IMPORT': {
        apiconfig.RESULT: 'docs',
        apiconfig.DIRECT: PRIMO_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"OBVSG"'}},
    },
}

BIBRECS = ('PRIMO_IMPORT',)
CONTRIBUTORS = ('GND_PERSON', 'GND_INSTITUTION', 'VIAF_PERSON', 'VIAF_INSTITUTION')

if 'uni-ak.ac.at' in SITE_URL:
    CONTRIBUTORS = tuple(x for x in ['ANGEWANDTE_PERSON', *CONTRIBUTORS])

if PELIAS_API_KEY:
    PLACES = ('PELIAS',)
elif GEONAMES_USER:
    PLACES = (
        'GND_PLACE',
        'GEONAMES_PLACE',
    )
else:
    PLACES = ('GND_PLACE',)


# if an autosuggest endpoint is not a key in this dict then the response of the API will be empty
ACTIVE_SOURCES = {
    'contributors': CONTRIBUTORS,
    'places': PLACES,
    'bibrecs': BIBRECS,
    'keywords': {'all': 'core.skosmos.get_base_keywords', 'search': 'core.skosmos.get_keywords'},
    'roles': 'core.skosmos.get_roles',
    'formats': 'core.skosmos.get_formats',
    'materials': 'core.skosmos.get_materials',
    'languages': 'core.skosmos.get_languages',
    'medialicenses': 'core.skosmos.get_media_licenses',
    'statuses': 'core.skosmos.get_statuses',
    'softwarelicenses': 'core.skosmos.get_software_licenses',
    'texttypes': 'core.skosmos.get_text_types',
    'types': 'core.skosmos.get_entry_types',
}

USER_QUOTA = env.int('USER_QUOTA', default=10 * 1024 * 1024 * 1024)  # user quota / year

CLAMAV_ENABLED = env.bool('CLAMAV_ENABLED', default=True)
CLAMAV_TCP_PORT = env.int('CLAMAV_TCP_PORT', default=3310)
CLAMAV_TCP_ADDR = f'{PROJECT_NAME}-clamav' if DOCKER else 'localhost'

LOOL_HOST = 'http://{}:9980'.format(f'{PROJECT_NAME}-lool' if DOCKER else 'localhost')

DOCS_USER = env('DOCS_USER', default=None)
DOCS_PASSWORD = env('DOCS_PASSWORD', default=None)

DOCS_REALM = 'base Portfolio Backend\'s Documentation'
DOCS_ROOT = os.path.join(BASE_DIR, '..', 'docs', 'build', 'html')  # noqa: F405
DOCS_URL = env('DOCS_URL', default='docs/')

if not os.path.exists(DOCS_ROOT):
    os.makedirs(DOCS_ROOT)

ARCHIVE_TYPE = env.str('ARCHIVE_TYPE', '')
ARCHIVE_SETTINGS = None
if ARCHIVE_TYPE:
    ARCHIVE_CREDENTIALS = {
        'USER': env.str(f'{ARCHIVE_TYPE}_USER'),
        'PWD': env.str(f'{ARCHIVE_TYPE}_PWD'),
    }
    ARCHIVE_URIS = {
        # end points created for media types with keys as mentioned in the media model
        'IDENTIFIER_BASE': env.str(f'{ARCHIVE_TYPE}_IDENTIFIER_BASE'),
        'IDENTIFIER_BASE_TESTING': env.str(f'{ARCHIVE_TYPE}_IDENTIFIER_BASE_TESTING'),
        'CREATE_URI': env.str(f'{ARCHIVE_TYPE}_CREATE_URI'),
        'BASE_URI': env.str(f'{ARCHIVE_TYPE}_BASE_URI'),
        'i': env.str(f'{ARCHIVE_TYPE}_BASE_URI') + env.str(f'{ARCHIVE_TYPE}_PICTURE_CREATE'),
        'v': env.str(f'{ARCHIVE_TYPE}_BASE_URI') + env.str(f'{ARCHIVE_TYPE}_VIDEO_CREATE'),
        'a': env.str(f'{ARCHIVE_TYPE}_BASE_URI') + env.str(f'{ARCHIVE_TYPE}_AUDIO_CREATE'),
        'd': env.str(f'{ARCHIVE_TYPE}_BASE_URI') + env.str(f'{ARCHIVE_TYPE}_DOCUMENT_CREATE'),
        'x': env.str(f'{ARCHIVE_TYPE}_BASE_URI') + env.str(f'{ARCHIVE_TYPE}_OBJECT_CREATE'),
    }
    ARCHIVE_METADATA_TEMPLATE = f'{ARCHIVE_TYPE.lower()}_container.json'
    ARCHIVE_THESIS_TEMPLATE = f'{ARCHIVE_TYPE.lower()}_thesis.json'

SYNC_TO_SHOWROOM = env.bool('SYNC_TO_SHOWROOM', default=False)
SHOWROOM_API_BASE = env.str('SHOWROOM_API_BASE', default=None)
SHOWROOM_API_KEY = env.str('SHOWROOM_API_KEY', default=None)
SHOWROOM_REPO_ID = env.int('SHOWROOM_REPO_ID', default=None)

if SYNC_TO_SHOWROOM:
    INSTALLED_APPS.append('showroom_connector')

USER_PREFERENCES_API_BASE = env.str('USER_PREFERENCES_API_BASE', default=None)
USER_PREFERENCES_API_KEY = env.str('USER_PREFERENCES_API_KEY', default=None)

# Sentry
SENTRY_DSN = env.str('SENTRY_DSN', default=None)
SENTRY_ENVIRONMENT = env.str(
    'SENTRY_ENVIRONMENT',
    default='development' if any([i in SITE_URL for i in ['dev', 'localhost', '127.0.0.1']]) else 'production',
)
SENTRY_TRACES_SAMPLE_RATE = env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.2)

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.rq import RqIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        integrations=[
            DjangoIntegration(),
            RedisIntegration(),
            RqIntegration(),
        ],
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=True,
    )
