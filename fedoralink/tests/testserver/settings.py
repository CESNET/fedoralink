import os

from django.utils.translation import ugettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SECRET_KEY = 'ct79($rugpit$d+d_t@b$m2t2(4bq)9bk^8^qv!ug%px8-^uxe'
DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'fedoralink',
    'fedoralink.tests',
    'fedoralink.tests.testserver.testapp'
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

MIDDLEWARE_CLASSES += [
    'fedoralink.middleware.FedoraUserDelegationMiddleware'
]

CONTEXT_PROCESSORS = [
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.template.context_processors.i18n',
    'django.template.context_processors.media',
    'django.template.context_processors.static',
    'django.template.context_processors.tz',
]

LANGUAGES = (
    ('cs', _('Čeština')),
    ('en', _('English')),
)

ROOT_URLCONF = 'fedoralink.tests.testserver.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': CONTEXT_PROCESSORS,
        },
    },
]

WSGI_APPLICATION = 'fedoralink.tests.testserver.wsgi.application'

REPO_URL='http://127.0.0.1:8080/fcrepo/rest'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, '../../../db.sqlite3'),
    },
    'repository': {
        'ENGINE': 'fedoralink.db',
        'REPO_URL': REPO_URL,
        'SEARCH_URL': 'http://127.0.0.1:9200/fedoralink-test',
        'USERNAME': '',
        'PASSWORD': '',
        'CONNECTION_OPTIONS': {
            'namespace': {
                'namespace': '',
                'prefix': 'test'
            }
        }
    }
}

DATABASE_ROUTERS = [
    'fedoralink.tests.testserver.routers.FedoraRouter',
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'


TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
