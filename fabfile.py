#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
from fabric.api import *
from fabric.tasks import Task

@task
def doctests():
    """Run the doctests found in GuessIt classes"""
    local('nosetests --with-doctest -vv pygoo')


class TestTask(Task):
    name = 'testtask'
    def __init__(self, testname, docstring):
        super(Task, self).__init__()
        self.name = 'test_' + testname
        self.__doc__ = 'Run the unittests for %s' % docstring

    def run(self):
        local('PYTHONPATH=. python tests/%s.py' % self.name)

test_basicnode = TestTask('basicnode', 'basic node functionality')
test_datamodel = TestTask('datamodel', 'ORM functionality')
test_advancedgraph = TestTask('advancedgraph', 'advanced graph operations')
test_inheritance = TestTask('inheritance', 'inheritance')
test_memory = TestTask('memory', 'memory-backed graphs')

@task
def unittests():
    """Run all the unittests"""
    EXCLUDE = ['test_pypi_sdist']
    def is_unittest(t):
        return t[0].startswith('test_') and t[0] not in EXCLUDE

    alltests = filter(is_unittest, globals().items())
    for name, testcase in alltests:
        testcase.run()


@task
def tests():
    """Run both the doctests and the unittests"""
    unittests()
    doctests()


@task
def clean_pyc():
    """Removes all the *.pyc files found in the repository"""
    local('find . -iname "*.pyc" -delete')


@task
def pylint():
    """Runs pylint on PyGoo's source code. Only show problems, no report"""
    local('pylint --reports=n --include-ids=y --disable=C,I,W0703 pygoo')


@task
def pylint_report():
    """Runs pylint on PyGoo's source code, full report"""
    local('pylint --include-ids=y --disable=C0103,C0111 pygoo')

def open_file(filename):
    """Open the given file using the OS's native programs"""
    if sys.platform.startswith('linux'):
        local('xdg-open "%s"' % filename)
    elif sys.platform == 'darwin':
        local('open "%s"' % filename)
    else:
        print 'Platform not supported:', sys.platform

@task
def doc():
    """Build the Sphinx documentation and open it in a web browser"""
    with lcd('docs'):
        local('make html')
        open_file('_build/html/index.html')

@task
def pypi_doc():
    """Builds the main page that will be uploaded to PyPI and open it in a
    web browser"""
    local('python setup.py --long-description | rst2html.py > /tmp/pygoo_pypi_doc.html')
    open_file('/tmp/pygoo_pypi_doc.html')


# Release management functions

@task
def set_version(version):
    """Set the version in the pygoo/__init__.py file"""
    initfile = open('pygoo/__init__.py').read()
    initfile = re.sub(r"__version__ = '\S*'",
                      r"__version__ = '%s'" % version,
                      initfile)
    open('pygoo/__init__.py', 'w').write(initfile)

@task
def upload_pypi():
    """Build and upload the package on PyPI"""
    local('python setup.py register sdist upload')

@task
def test_pypi_sdist():
    """Build the PyPI package and test whether it is installable and passes
    the tests"""
    d = '_tmp_pypi_pygoo'
    local('rm -fr dist %s' % d)
    local('python setup.py sdist')
    local('virtualenv %s' % d)
    with lcd(d):
        with prefix('source bin/activate'):
            local('pip install ../dist/*')
            #local('pip install PyYaml') # to be able to run the tests
            #local('cp ../tests/*.py ../tests/*.yaml ../tests/*.txt .')
            #local('python test_autodetect.py')
            #local('python test_movie.py')
            #local('python test_episode.py')
            #local('python test_language.py')
    local('rm -fr %s' % d)
