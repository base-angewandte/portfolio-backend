"""
Django settings for portfolio project.

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
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from hashids import Hashids
from apimapper import config as apiconfig

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
TESTING = any(test in sys.argv for test in (
    'test', 'csslint', 'jenkins', 'jslint',
    'jtest', 'lettuce', 'pep8', 'pyflakes',
    'pylint', 'sloccount',
))

DOCKER = env.bool('DOCKER', default=True)

SITE_URL = env.str('SITE_URL')

FORCE_SCRIPT_NAME = env.str('FORCE_SCRIPT_NAME', default='/portfolio')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[urlparse(SITE_URL).hostname])

BEHIND_PROXY = env.bool('BEHIND_PROXY', default=True)

ADMINS = getaddresses([env('DJANGO_ADMINS', default='Philipp Mayer <philipp.mayer@uni-ak.ac.at>')])

MANAGERS = ADMINS

SUPERUSERS = env.tuple('SUPERUSERS', default=(
    '***REMOVED***',  # Philipp Mayer
))

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
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django_cas_ng.backends.CASBackend',
]

LOGIN_URL = reverse_lazy('cas_ng_login')
LOGOUT_URL = reverse_lazy('cas_ng_logout')

CAS_SERVER_URL = env.str('CAS_SERVER', default='{}cas/'.format(SITE_URL))
CAS_LOGIN_MSG = None
CAS_LOGGED_MSG = None
CAS_RENEW = False
CAS_LOGOUT_COMPLETELY = True
CAS_RETRY_LOGIN = True
CAS_VERSION = '3'
CAS_APPLY_ATTRIBUTES_TO_USER = True
CAS_REDIRECT_URL = env.str('CAS_REDIRECT_URL', default=FORCE_SCRIPT_NAME or '/')
CAS_RENAME_ATTRIBUTES = {
    'firstName': 'first_name',
    'lastName': 'last_name',
    'email0': 'email',
}

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
    MIDDLEWARE += ['general.middleware.SetRemoteAddrFromForwardedFor', ]
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ROOT_URLCONF = '{}.urls'.format(PROJECT_NAME)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
            'string_if_invalid': "[invalid variable '%s'!]" if DEBUG else "",
        },
    },
]

WSGI_APPLICATION = '{}.wsgi.application'.format(PROJECT_NAME)


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('POSTGRES_DB', 'django_{}'.format(PROJECT_NAME)),
        'USER': os.environ.get('POSTGRES_USER', 'django_{}'.format(PROJECT_NAME)),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'password_{}'.format(PROJECT_NAME)),
        'HOST': '{}-postgres'.format(PROJECT_NAME) if DOCKER else 'localhost',
        'PORT': '5432',
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

STATICFILES_DIRS = (
    '{}{}'.format(os.path.normpath(os.path.join(BASE_DIR, 'static')), os.sep),
)
STATIC_URL = '{}/s/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
STATIC_ROOT = '{}{}'.format(os.path.normpath(os.path.join(BASE_DIR, 'assets', 'static')), os.sep)

MEDIA_URL = '{}/m/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
MEDIA_ROOT = '{}{}'.format(os.path.normpath(os.path.join(BASE_DIR, 'assets', 'media')), os.sep)

PROTECTED_MEDIA_URL = '{}/p/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
PROTECTED_MEDIA_ROOT = '{}{}'.format(os.path.normpath(os.path.join(BASE_DIR, 'assets', 'protected')), os.sep)
PROTECTED_MEDIA_LOCATION = '{}/internal/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
PROTECTED_MEDIA_SERVER = 'nginx' if not DEBUG else 'django'

""" Logging """
LOG_DIR = os.path.join(BASE_DIR, '..', 'logs')

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'simple_with_time': {
            'format': '%(levelname)s %(asctime)s %(message)s',
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'application.log'),
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 1000,
            'use_gzip': True,
            'delay': True,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'stream_to_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'rq_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple_with_time',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file', 'mail_admins'],
            'propagate': True,
            'level': 'INFO',
        },
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'rq.worker': {
            'handlers': ['rq_console', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}

""" Cache settings """
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://{}:6379/0'.format('{}-redis'.format(PROJECT_NAME) if DOCKER else 'localhost'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

RQ_QUEUES = {
    'default': {
        'USE_REDIS_CACHE': 'default',
        'DEFAULT_TIMEOUT': 500,
    },
    'high': {
        'USE_REDIS_CACHE': 'default',
    },
}

if DEBUG or TESTING:
    for queueConfig in iter(RQ_QUEUES.values()):
        queueConfig['ASYNC'] = False

RQ_EXCEPTION_HANDLERS = ['general.rq.handlers.exception_handler']


""" Session settings """
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_NAME = 'sessionid_{}'.format(PROJECT_NAME)
SESSION_COOKIE_DOMAIN = env.str('SESSION_COOKIE_DOMAIN', default=None)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CSRF_COOKIE_NAME = 'csrftoken_{}'.format(PROJECT_NAME)
CSRF_COOKIE_DOMAIN = env.str('CSRF_COOKIE_DOMAIN', default=None)
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

CORS_ALLOW_CREDENTIALS = env.bool('CORS_ALLOW_CREDENTIALS', default=False)
CORS_ORIGIN_ALLOW_ALL = env.bool('CORS_ORIGIN_ALLOW_ALL', default=False)
CORS_ORIGIN_WHITELIST = env.list('CORS_ORIGIN_WHITELIST', default=[])
CORS_URLS_REGEX = r'^/(api|autosuggest)/.*$'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
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
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {}
}

OPEN_API_VERSION = env.str('OPEN_API_VERSION', default='2.0')
ACTIVE_SCHEMAS = env.list(
    'ACTIVE_SCHEMAS',
    default=[
        'architecture',
        'audio',
        'award',
        'concert',
        'conference',
        'document',
        'event',
        'exhibition',
        'performance',
        'festival',
        'image',
        'research_project',
        'sculpture',
        'software',
        'video',
        'workshop',
    ]
)

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(
        MIDDLEWARE.index('django.contrib.sessions.middleware.SessionMiddleware'),
        'debug_toolbar.middleware.DebugToolbarMiddleware'
    )
    INTERNAL_IPS = ('127.0.0.1', )

SKOSMOS_API = 'https://voc.uni-ak.ac.at/skosmos/rest/v1/'
VOC_ID = 'povoc'
VOC_GRAPH = 'http://base.uni-ak.ac.at/portfolio/vocabulary/'

LANGUAGES_VOCID = 'languages'

# Autosuggest
SOURCES = {
    'ANGEWANDTE_PERSON': {
        apiconfig.URL: '{}api/persons'.format(SITE_URL),
        apiconfig.QUERY_FIELD: 'searchstring',
        apiconfig.PAYLOAD: None,
    },
    'GND_PERSON': {
        apiconfig.URL: 'https://lobid.org/gnd/search',
        apiconfig.QUERY_FIELD: 'q',
        apiconfig.PAYLOAD: {
            'format': 'json:suggest',
            'filter': 'type:Person',
        }
    },
    'GND_INSTITUTION': {
        apiconfig.URL: 'https://lobid.org/gnd/search',
        apiconfig.QUERY_FIELD: 'q',
        apiconfig.PAYLOAD: {
            'format': 'json:suggest',
            'filter': 'type:CorporateBody',
        }
    },
    'VIAF_PERSON': {
        apiconfig.URL: 'http://www.viaf.org/viaf/AutoSuggest',
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.PAYLOAD: None,
    },
    'GND_PLACE': {
        apiconfig.URL: 'https://lobid.org/gnd/search',
        apiconfig.QUERY_FIELD: 'q',
        apiconfig.PAYLOAD: {
            'format': 'json:suggest',
            'filter': 'type:PlaceOrGeographicName',
        }
    },
    'VIAF_PLACE': {
        apiconfig.URL: 'http://www.viaf.org/viaf/AutoSuggest',
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.PAYLOAD: None,
    },
    'GEONAMES_PLACE': {
        apiconfig.URL: 'http://api.geonames.org/search',
        apiconfig.QUERY_FIELD: 'q',
        apiconfig.PAYLOAD: {
            'maxRows': 10,
            'username': '***REMOVED***',
            'type': 'json',
        }
    },
    'BASE_KEYWORDS': {
        apiconfig.URL: '{}basekw/search'.format(SKOSMOS_API),
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'lang': get_language_lazy(),
            'group': 'http://base.uni-ak.ac.at/recherche/keywords/collection_base',
        },
    },
    'VOC_KEYWORDS': {
        apiconfig.URL: '{}disciplines/search'.format(SKOSMOS_API),
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'lang': get_language_lazy(),
        },
    },
    'VOC_ROLES': {
        apiconfig.URL: '{}povoc/search'.format(SKOSMOS_API),
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'lang': get_language_lazy(),
            'parent': 'http://base.uni-ak.ac.at/portfolio/vocabulary/role',
            'unique': True,
        }
    },
    'VOC_FORMATS': {
        apiconfig.URL: '{}povoc/search'.format(SKOSMOS_API),
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'lang': get_language_lazy(),
            'parent': 'http://base.uni-ak.ac.at/portfolio/vocabulary/format_type',
            'unique': True,
        }
    },
    'VOC_MATERIALS': {
        apiconfig.URL: '{}povoc/search'.format(SKOSMOS_API),
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'lang': get_language_lazy(),
            'parent': 'http://base.uni-ak.ac.at/portfolio/vocabulary/material_type',
            'unique': True,
        }
    },
    'VOC_LANGUAGES': {
        apiconfig.URL: '{}languages/search'.format(SKOSMOS_API),
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'lang': get_language_lazy(),
            'unique': True,
        }
    },
    'VOC_TEXTTYPES': {
        apiconfig.URL: '{}povoc/search'.format(SKOSMOS_API),
        apiconfig.QUERY_FIELD: 'query',
        apiconfig.QUERY_SUFFIX_WILDCARD: True,
        apiconfig.PAYLOAD: {
            'lang': get_language_lazy(),
            'parent': 'http://base.uni-ak.ac.at/portfolio/vocabulary/text_type',
            'unique': True,
        }
    },
}

ANGEWANDTE_MAPPING = {
    'source': 'id',
    'name': 'name',
}
GND_CONTRIBUTORS_MAPPING = {
    'source': 'id',  # common_schema: GND schema
    'name': 'label',
}
GND_PLACES_MAPPING = {
    'source': 'id',  # common_schema: GND schema
    'name': 'label',
}
VIAF_CONTRIBUTORS_MAPPING = {
    'name': 'displayForm',
}
VIAF_PLACES_MAPPING = {
    'name': 'toponymName',
}
GEONAMES_MAPPING = {
    'name': 'toponymName',
}
BASE_KEYWORDS_MAPPING = {
    'source': 'uri',
    'keyword': 'prefLabel',
}
VOC_KEYWORDS_MAPPING = {
    'source': 'uri',
    'keyword': 'prefLabel',
}
VOC_MAPPING = {
    'source': 'uri',
    'label': 'prefLabel',
}

RESPONSE_MAPS = {
    'ANGEWANDTE_PERSON': {
        apiconfig.RESULT: 'users',
        apiconfig.DIRECT: ANGEWANDTE_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"Angewandte"'}},
    },
    'GND_PERSON': {
        apiconfig.DIRECT: GND_CONTRIBUTORS_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"GND"'}},
    },
    'GND_INSTITUTION': {
        apiconfig.DIRECT: GND_CONTRIBUTORS_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"GND"'}},
    },
    'VIAF_PERSON': {
        apiconfig.RESULT: 'result',
        apiconfig.FILTER: {'nametype': 'personal'},
        apiconfig.DIRECT: VIAF_CONTRIBUTORS_MAPPING,
        apiconfig.RULES: {
            'source_name': {apiconfig.RULE: '"VIAF"'},
            'source': {
                apiconfig.RULE: '"http://www.viaf.org/viaf/{p1}"',
                apiconfig.FIELDS: {'p1': 'viafid'},
            },
        }
    },
    'GND_PLACE': {
        apiconfig.DIRECT: GND_PLACES_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"GND"'}},
    },
    'VIAF_PLACE': {
        apiconfig.RESULT: 'result',
        apiconfig.FILTER: {'nametype': 'geographic'},
        apiconfig.DIRECT: VIAF_PLACES_MAPPING,
        apiconfig.RULES: {
            'source_name': {apiconfig.RULE: '"VIAF"'},
            'source': {
                apiconfig.RULE: '"http://www.viaf.org/viaf/{p1}"',
                apiconfig.FIELDS: {'p1': 'viafid'},
            },
        }
    },
    'GEONAMES_PLACE': {
        apiconfig.RESULT: 'geonames',
        apiconfig.DIRECT: GEONAMES_MAPPING,
        apiconfig.RULES: {
            'source_name': {apiconfig.RULE: '"GEONAMES"'},
            'source': {
                apiconfig.RULE: '"http://api.geonames.org/get?username=***REMOVED***&geonameId={p1}"',
                apiconfig.FIELDS: {'p1': 'geonameId'},
            },
        }
    },
    'BASE_KEYWORDS': {
        apiconfig.RESULT: 'results',
        apiconfig.DIRECT: BASE_KEYWORDS_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"base"'}},
    },
    'VOC_KEYWORDS': {
        apiconfig.RESULT: 'results',
        apiconfig.DIRECT: VOC_KEYWORDS_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"voc"'}},
    },
    'VOC_ROLES': {
        apiconfig.RESULT: 'results',
        apiconfig.DIRECT: VOC_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"portfolio"'}},
    },
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
    'VOC_TEXTTYPES': {
        apiconfig.RESULT: 'results',
        apiconfig.DIRECT: VOC_MAPPING,
        apiconfig.RULES: {'source_name': {apiconfig.RULE: '"portfolio"'}},
    },
}

# if an autosuggest endpoint is not a key in this dict then the response of the API will be empty
ACTIVE_SOURCES = {
    'contributors': ('ANGEWANDTE_PERSON', 'VIAF_PERSON', 'GND_PERSON', 'GND_INSTITUTION'),
    'places': ('GND_PLACE', 'GEONAMES_PLACE'),
    'keywords': {
        'all': 'core.skosmos.get_base_keywords',
        'search': 'core.skosmos.get_keywords',
    },
    'roles': 'core.skosmos.get_roles',
    'formats': 'core.skosmos.get_formats',
    'materials': 'core.skosmos.get_materials',
    'languages': 'core.skosmos.get_languages',
    'licenses': (),
    'texttypes': 'core.skosmos.get_text_types',
    'types': 'core.skosmos.get_entry_types',
}

USER_QUOTA = env.int('USER_QUOTA', default=1024 * 1024 * 1024)  # user quota / year

LOOL_HOST = 'http://{}:9980'.format('{}-lool'.format(PROJECT_NAME) if DOCKER else 'localhost')
