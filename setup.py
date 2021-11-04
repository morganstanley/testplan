#!/usr/bin/env python
"""
Setup testplan and dependencies.
"""
import ast
import sys
from pathlib import Path, PurePosixPath

from setuptools import setup, find_packages


REQUIRED = [
    "sphinx<2",
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
    "marshmallow==3.11.1",
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
    "rpyc",
]

WEB_UI_PACKAGE_DIR = "testplan/web_ui/"
VERSION_FILE = "testplan/version.py"

ui_files = [
    str(PurePosixPath(p).relative_to(WEB_UI_PACKAGE_DIR))
    for p in Path(WEB_UI_PACKAGE_DIR).glob("testing/build/**/*")
]


def get_version():
    # we use ast here to avoid import
    class VersionFinder(ast.NodeVisitor):
        def __init__(self):
            self.version = None

        def visit_Assign(self, node: ast.Assign):
            if node.targets[0].id == "__version__":
                # python 3.7 node.value is ast.Str from 3.8 it seem it is ast.Constant
                self.version = (
                    node.value.value
                    if isinstance(node.value, ast.Constant)
                    else node.value.s
                )

    module = ast.parse(Path("testplan/version.py").read_text())

    version_visitor = VersionFinder()
    version_visitor.visit(module)
    return version_visitor.version


setup(
    name="testplan",
    version=get_version(),
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
