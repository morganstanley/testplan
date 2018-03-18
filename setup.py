#!/usr/bin/env python

import sys

from setuptools import setup, find_packages

required = [
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
    'numpy',
    'pyparsing',
    'cycler',
    'matplotlib',
    'Pillow',
 ]
if sys.version_info[0] == 2:
    required.append('functools32')

install_optional = True
if install_optional is True:
    required.extend(
        ['sklearn',
         'scipy',
         'sphinx',
         'sphinx_rtd_theme'])

setup(name='Testplan',
  version='1.0',
  description='Testplan testing framework',
  author='',
  author_email='eti-testplan@morganstanley.com',
  url='https://github.com/Morgan-Stanley/testplan',
  packages=['testplan'] + find_packages(),
  install_requires=required
 )
