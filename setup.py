#!/usr/bin/env python
"""
Setup testplan and dependencies.
"""

import sys
from pathlib import Path, PurePosixPath

from setuptools import setup, find_packages


REQUIRED = [
    "sphinx",
    "sphinx_rtd_theme",
    "setuptools",
    "pytest",
    "py",
    "psutil",
    "schema",
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
    "flask<2.0.0",
    "flask_restplus",
    "cheroot",
    "validators==0.14.0",
    "ipaddress",
    "Werkzeug<1.0.0",
    "boltons",
    "Pillow",
    "plotly",
]

WEB_UI_PACKAGE_DIR = "testplan/web_ui/"

ui_files = [
    str(PurePosixPath(p).relative_to(WEB_UI_PACKAGE_DIR))
    for p in Path(WEB_UI_PACKAGE_DIR).glob("testing/build/**/*")
]

print(ui_files)

setup(
    name="testplan",
    version="1.0.0",
    description="Testplan testing framework",
    author="",
    author_email="eti-testplan@morganstanley.com",
    url="https://github.com/morganstanley/testplan",
    include_package_data=True,
    packages=find_packages(include=("testplan*",)),
    package_dir={"testplan": "testplan"},
    package_data={"testplan.web_ui": ui_files},
    install_requires=REQUIRED,
    python_requires=">=3.7",
    entry_points={"console_scripts": ["tpsreport=testplan.cli.tpsreport:cli"]},
)
