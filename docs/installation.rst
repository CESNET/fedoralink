Installation and Configuration
==============================

1. Install fedoralink:

.. code-block:: bash
    :emphasize-lines: 4

    virtualenv testfedora-venv -p python3
    source testfedora-venv/bin/activate
    pip install django
    pip install git+https://github.com/CESNET/fedoralink.git
    django-admin startproject testfedora

2. Add fedoralink to ``INSTALLED_APPS`` at the end of the settings.py file::

    INSTALLED_APPS += [
        'fedoralink'
    ]

3. Add database to ``settings.py``. Replace REPO_URL with path to Fedora Repository and SEARCH_URL
   to an index inside elasticsearch. If the index does not exist, it will be created::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, '../../../db.sqlite3'),
        },
        'repository': {
            'ENGINE': 'fedoralink.db',
            'REPO_URL': 'http://127.0.0.1:8080/fcrepo/rest',
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

4. Set up a database router that will direct registered fedora models into fedora database::

    DATABASE_ROUTERS = [
        'fedoralink.db.routers.FedoraRouter',
    ]

   This step is optional but if the router is not registered you will have to route the models
   to fedora repository yourself and namespace-based routing will not be available.

5. Check that the setup works::

    export DJANGO_SETTINGS_MODULE=testfedora.settings
    python3
    from fedoralink.models import FedoraObject

    # empty pk is the root of the repository
    list(FedoraObject.objects.filter(pk=''))

