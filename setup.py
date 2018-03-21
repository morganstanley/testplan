#!/usr/bin/env python
'''
Setup testplan and dependencies.

Example usage:
  # Basic setup - some functionality missing
  $ python setup.py install

  # Full setup
  $ python setup.py install --type full
'''

import sys

from setuptools import setup, find_packages
from setuptools.command import easy_install
from distutils.core import Command

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
]

class InstallCommand(Command):
    description = 'Install Testplan.'
    user_options = [
        ('type=', None, '[basic, full]')
    ]

    def initialize_options(self):
        self.type = None

    def finalize_options(self):
        assert self.type in (None, 'basic', 'full'), 'Invalid setup type!'

    def run(self):
        if self.type == 'full':
            easy_install.main([
                'sklearn',
                'numpy',
                'matplotlib',
                'scipy',
                'sphinx',
                'sphinx_rtd_theme'
            ])


setup(name='Testplan',
  version='1.0',
  description='Testplan testing framework',
  author='',
  author_email='eti-testplan@morganstanley.com',
  url='https://github.com/Morgan-Stanley/testplan',
  packages=['testplan'] + find_packages(),
  cmdclass={'install': InstallCommand},
  install_requires=REQUIRED
 )
