#!/usr/bin/env python
"""
Setup testplan and dependencies.
"""

import sys

from setuptools import setup, find_packages


REQUIRED = [
    "sphinx",
    "sphinx_rtd_theme",
    "setuptools",
    "pytest",
    "py",
    "psutil",
    "schema<0.7.0",
    "pytz",
    "lxml",
    "python-dateutil",
    "reportlab",
    "marshmallow==3.0.0b2",
    "termcolor",
    "colorama",
    "pyzmq",
    "terminaltables",
    "pyparsing",
    "cycler",
    "matplotlib",
    "numpy",
    "scipy",
    "requests>=2.4.3",
    "flask",
    "flask_restplus",
    "cheroot",
    "validators==0.14.0",
    "ipaddress",
    "Werkzeug<1.0.0",
    "boltons",
    "Pillow",
]

setup(
    name="Testplan",
    version="1.0",
    description="Testplan testing framework",
    author="",
    author_email="eti-testplan@morganstanley.com",
    url="https://github.com/morganstanley/testplan",
    packages=["testplan"] + find_packages(),
    include_package_data=True,
    install_requires=REQUIRED,
    scripts=["install-testplan-ui"],
)
