# fedoralink
Django access classes for Fedora Commons 4

Installation:

### 1. Create a new django project with a Python 3 virtual environment

```bash
cd /tmp
virtualenv testfedora-venv -p python3
. /tmp/testfedora-venv/bin/activate
pip install django
pip install git+https://github.com/CESNET/fedoralink.git
django-admin startproject testfedora
```

### 2. Add fedoralink into INSTALLED_APPS in settings.py:
```python
INSTALLED_APPS += [
    'fedoralink'
]
```
### 3. Add repository/ies and database router into settings.py:
```python
DATABASES['repository'] = {
    'ENGINE'            : 'fedoralink.db',
    'SEARCH_ENGINE'     : 'fedoralink.indexer.SOLRIndexer',
    'REPO_URL'          : 'http://127.0.0.1:8080/fcrepo/rest',
    'SEARCH_URL'        : 'http://127.0.0.1:9200/testfedora',
    'USERNAME'          : 'fedoralink',
    'PASSWORD'          : 'fedoralink',
    'CONNECTION_OPTIONS': {
        'namespace': {
            'namespace': '',
            'prefix': ''
        }
    }
}

DATABASE_ROUTERS = [
    'fedoralink.tests.testserver.routers.FedoraRouter',
]
```

### 4. To test:

bash:
```bash
export DJANGO_SETTINGS_MODULE=testfedora.settings
python3
```

inside python:
```python
import django
django.setup()
from fedoralink.models import FedoraObject
# empty fedora_id is the root of the repository
FedoraObject.objects.filter(fedora_id='')
    INFO:elasticsearch:HEAD http://127.0.0.1:9200/testfedora_test [status:200 request:0.012s]
    INFO:elasticsearch:POST http://127.0.0.1:9200/testfedora_test/_refresh [status:200 request:0.004s]
    INFO:elasticsearch:GET http://127.0.0.1:9200/testfedora_test/_search?scroll=1m&size=1000&from=0 [status:200 request:0.005s]
    INFO:elasticsearch:DELETE http://127.0.0.1:9200/_search/scroll [status:200 request:0.003s]

```

### 5. Simple operations

#### Create and save a fedora object

1) Define a fedora annotated model in models.py:

```python
from django.db.models import Model, TextField
from fedoralink.fedorans import CESNET
from fedoralink.models import fedora
 
@fedora(namespace=CESNET)
class TestObject(Model):
    text = TextField(null=True, blank=True)
```

2) Make migrations for your defined model:
```bash
python manage.py makemigrations testfedora
Migrations for 'testfedora':
  testfedora/migrations/0001_initial.py
    - Create model TestObject

```

3) Apply created migrations:
```bash
python manage.py migrate testfedora --database repository
Operations to perform:
  Apply all migrations: testfedora
Running migrations:
  Applying testfedora.0001_initial... OK
```

4) Create object instance and store it in Fedora:
```python
import django
django.setup()
INFO:rdflib:RDFLib Version: 4.2.2
from testfedora.models import TestObject
TestObject.objects.create(text='Hello World!')
<TestObject: TestObject object>
```

