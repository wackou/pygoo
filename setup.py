from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


version = '0.1a1'

install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
]


setup(name = 'pygoo',
      version = version,
      description = "PyGoo is an Object-Graph mapper, similar to SQLAlchemy but for graph DBs",
      long_description = README + '\n\n' + NEWS,
      classifiers = [], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords = 'pygoo object graph mapper',
      author = 'Nicolas Wack',
      author_email = 'wackou@gmail.com',
      url = 'http://gitorious.org/pygoo',
      license = 'GPLv3',
      packages = find_packages(exclude = [ 'ez_setup', 'examples', 'tests' ]),
      include_package_data = True,
      zip_safe = False,
      install_requires = install_requires,
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
