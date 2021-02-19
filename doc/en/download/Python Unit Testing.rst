Python Unit Testing
*******************

.. _example_pyunit:

PyUnit
------

PyUnit is the unit-testing framework built into the Python standard library,
see https://docs.python.org/3.7/library/unittest.html for more information.
PyUnit testcases may be integrated with a Testplan via the PyUnit test runner.

Required files:
  - :download:`test_plan.py <../../../examples/PyUnit/test_plan.py>`

test_plan.py
++++++++++++
.. literalinclude:: ../../../examples/PyUnit/test_plan.py

.. _example_pytest:

PyTest
------

PyTest is a very popular python testing framework, which offers more advanced
features than the standard library PyUnit framework. See
https://docs.pytest.org/en/latest/ for more information. You can integrate
PyTest testcases with your testplan via the PyTest test runner.

Required files:
  - :download:`test_plan.py <../../../examples/PyTest/test_plan.py>`
  - :download:`pytest_tests.py <../../../examples/PyTest/pytest_tests.py>`

test_plan.py
++++++++++++
.. literalinclude:: ../../../examples/PyTest/test_plan.py

pytest_tests.py
+++++++++++++++

.. literalinclude:: ../../../examples/PyTest/pytest_tests.py

