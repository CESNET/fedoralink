#This file mainly exists to allow python setup.py test to work.
import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'fedoralink.tests.testserver.settings'
test_dir = os.path.dirname(__file__)
sys.path.insert(0, test_dir)

import subprocess

from django.test.utils import get_runner
from django.conf import settings

def runtests():
    # test_runner_class = get_runner(settings)
    # runner = test_runner_class(verbosity=1, interactive=True)
    # suite = runner.build_suite()
    # failures = runner.run_suite(suite)
    # sys.exit(failures)

    ret = subprocess.call(['coverage', 'run', 'fedoralink/tests/testserver/manage.py', 'test', '--logging-level=DEBUG'])
    ret2 = subprocess.call(['coverage', 'html'])
    ret1 = subprocess.call(['coverage', 'report'])
    sys.exit(ret + ret1 + ret2)

if __name__ == '__main__':
    runtests()