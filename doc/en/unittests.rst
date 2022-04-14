.. _UnitTests:

Unit Tests
**********

Testplan has full support for external testing frameworks - allowing for seamless integration with
GTest, JUnit, PyTest and more.

Unit tests are written as normal, in the framework of choice, allowing developers to continue to work
in a native environment that they are familiar with, and allowing for manual running of tests from
within IDEs during development, but are also added to a Testplan plan in the same way that a MultiTest
is added.

The Testplan script will then executed unit tests, either in current process (typically for python tests)
or as a subprocess (for unit tests of other languages), and include their result in test report.

CPP - CppUnit
=============

CppUnit is no longer being developed, and is only included to support those projects that already have
CppUnit tests written. The integration of CppUnit is via the :py:class:`~testplan.testing.cpp.cppunit.Cppunit`
runner, and example can be found :ref:`here <example_cppunit>`.

CPP - GoogleTest
================

Google's C++ test framework that has many features including support for mocking, see
https://github.com/google/googletest for more information. It is integrated with Testplan via the
:py:class:`~testplan.testing.cpp.gtest.GTest` runner. Example can be found :ref:`here <example_gtest>`.


Java - JUnit
============

JUnit 5 is the next generation of JUnit. The goal is to create an up-to-date foundation
for developer-side testing on the JVM. This includes focusing on Java 8 and above, as well as enabling many
different styles of testing. see https://junit.org/junit5/ for more information. It is integrated with Testplan via the
:py:class:`~testplan_ms.testing.junit.JUnit` runner. Example can be found :ref:`here <example_junit>`.


Python - unittest
=================

``unittest`` is the unit-testing framework built into the Python standard library,
see https://docs.python.org/3.7/library/unittest.html for more information.
``unittest`` testcases may be integrated with Testplan via the :py:class:`~testplan.testing.pyunit.PyUnit`
test runner. Example can be found :ref:`here <example_pyunit>`.

Python - pytest
===============

``pytest`` is a very popular python testing framework, which offers more advanced
features than the standard library unittest framework. See
https://docs.pytest.org/en/latest/ for more information. You can integrate
``pytest`` testcases with your testplan via the :py:class:`~testplan.testing.py_test.PyTest`
test runner. Example can be found :ref:`here <example_pytest>`.
