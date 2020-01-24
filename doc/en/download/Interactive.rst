Interactive
***********

In addition to the default batch mode for running tests, Testplan also allows
tests and their environments to be run in an "interactive" mode. Currently
only the backend HTTP (REST) API is implemented. The examples below show
different ways you can connect to Testplan's interactive API. Though
powerful and flexible, API access is a feature suitable for more advanced
users that are happy to build their own client. We are currently working on a
web page front-end that will allow user-friendly control of tests and their
environments - watch this space for updates soon!

.. _example_interactive_basic:

Basic
-----

Required files:
  - :download:`test_plan.py <../../../examples/Interactive/Basic/test_plan.py>`
  - :download:`my_tests/__init__.py <../../../examples/Interactive/Basic/my_tests/__init__.py>`
  - :download:`my_tests/mtest.py <../../../examples/Interactive/Basic/my_tests/mtest.py>`
  - :download:`my_tests/basic.py <../../../examples/Interactive/Basic/my_tests/basic.py>`
  - :download:`my_tests/tcp.py <../../../examples/Interactive/Basic/my_tests/tcp.py>`
  - :download:`my_tests/dependency.py <../../../examples/Interactive/Basic/my_tests/dependency.py>`

test_plan.py
++++++++++++
.. literalinclude:: ../../../examples/Interactive/Basic/test_plan.py

my_tests/mtest.py
+++++++++++++++++
.. literalinclude:: ../../../examples/Interactive/Basic/my_tests/mtest.py

