Usage
=====

Installation and Configuration
------------------------------

1. Install fedoralink::

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

5. Check that the setup works::

    export DJANGO_SETTINGS_MODULE=testfedora.settings
    python3
    from fedoralink.models import FedoraObject

    # empty pk is the root of the repository
    list(FedoraObject.objects.filter(pk=''))

6. Start writing your custom model

Writing fedora database models
------------------------------

Fedora database model looks completely same as any other Django model. In fact, with a database router,
any Django model can be stored inside Fedora Repository. The following model fields are currently supported:

 * ``AutoField``
 * ``CharField``
 * ``IntegerField``
 * ``FloatField``
 * ``DateTimeField``

Sample models.py::

    @fedora(namespace=CESNET)
    class Simple(models.Model):
        pass

The annotation is optional. If used:

 * the model is automatically routed to the *'repository'* database unless defined otherwise
 * defines the RDF namespace within which fields are created
 * defines the RDF types that are associated with the python class (see the mapping details)
 * to route to a different database, pass django's *'using'* definition in meta or manager methods

If the annotation is not used:
 * the model gets the CESNET rdf namespace and CESNET:modelname rdf:type
 * it is not routed to fedora repository. To make the routing, pass the database via
   *'using'* definition in meta or manager methods or a custom router

After the model is created, run::

    python manage.py makemigrations <myapp>
    python manage.py migrate --database repository <myapp>