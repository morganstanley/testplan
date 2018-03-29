#!/usr/bin/env python
'''
Setup testplan and dependencies.
'''

import sys

from setuptools import setup, find_packages


REQUIRED = [
    'pytest',
    'py',
    'psutil',
    'six',
    'future',
    'setuptools',
    'schema',
    'pytz',
    'lxml',
    'python-dateutil',
    'reportlab',
    'marshmallow==3.0.0b2',
    'mock',
    'termcolor',
    'colorama',
    'enum34',
    'pyzmq',
    'terminaltables',
    'pyparsing',
    'cycler',
    'scipy',
    'sklearn',
    'numpy',
    'matplotlib',
    'sphinx',
    'sphinx_rtd_theme',
    'requests>=2.4.3'
]


setup(name='Testplan',
  version='1.0',
  description='Testplan testing framework',
  author='',
  author_email='eti-testplan@morganstanley.com',
  url='https://github.com/Morgan-Stanley/testplan',
  packages=['testplan'] + find_packages(),
  install_requires=REQUIRED
 )

