.. _example_execution_pools:

Execution Pools
***************

.. _example_pool_thread:

Thread pool
-----------

Required files:
  - :download:`test_plan.py <../../../examples/ExecutionPools/Thread/test_plan.py>`
  - :download:`tasks.py <../../../examples/ExecutionPools/Thread/tasks.py>`

test_plan.py
++++++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Thread/test_plan.py

tasks.py
+++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Thread/tasks.py


.. _example_pool_process:

Process pool
------------

Required files:
  - :download:`test_plan.py <../../../examples/ExecutionPools/Process/test_plan.py>`
  - :download:`tasks.py <../../../examples/ExecutionPools/Process/tasks.py>`

test_plan.py
++++++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Process/test_plan.py

tasks.py
+++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Process/tasks.py

.. _example_pool_remote:

Remote pool
-----------

Required files:
  - :download:`test_plan.py <../../../examples/ExecutionPools/Remote/test_plan.py>`
  - :download:`tasks.py <../../../examples/ExecutionPools/Remote/tasks.py>`
  - :download:`setup_script.ksh <../../../examples/ExecutionPools/Remote/setup_script.ksh>`

test_plan.py
++++++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Remote/test_plan.py

tasks.py
+++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Remote/tasks.py

setup_script.ksh
++++++++++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Remote/setup_script.ksh

.. _example_task_rerun:

Task Rerun
----------

Required files:
  - :download:`test_plan.py <../../../examples/ExecutionPools/Rerun/test_plan.py>`
  - :download:`tasks.py <../../../examples/ExecutionPools/Rerun/tasks.py>`

test_plan.py
++++++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Rerun/test_plan.py

tasks.py
+++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Rerun/tasks.py

.. _example_multiTest_parts:

MultiTest parts scheduling
--------------------------

Required files:
  - :download:`test_plan.py <../../../examples/ExecutionPools/Parts/test_plan.py>`
  - :download:`tasks.py <../../../examples/ExecutionPools/Parts/tasks.py>`

test_plan.py
++++++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Parts/test_plan.py

tasks.py
+++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Parts/tasks.py

.. _example_discover:

Task discover
-------------
This example requires a file structure demonstrated as below. In this example,
@task_target annotated functions defined under sub-projects will be discovered
when plan.schedule_all is called, without requiring user to specify target/module/path
separately for each task.

| |~sub_proj1/
| | |-__init__.py
| | |-suites.py
| | `-tasks.py
| |~sub_proj2/
| | |-__init__.py
| | |-suites.py
| | `-tasks.py
| `-test_plan.py*

Required files:
  - :download:`test_plan.py <../../../examples/ExecutionPools/Discover/test_plan.py>`
  - :download:`sub_proj1/__init__.py <../../../examples/ExecutionPools/Discover/sub_proj1/__init__.py>`
  - :download:`sub_proj1/suites.py <../../../examples/ExecutionPools/Discover/sub_proj1/suites.py>`
  - :download:`sub_proj1/tasks.py <../../../examples/ExecutionPools/Discover/sub_proj1/tasks.py>`
  - :download:`sub_proj2/__init__.py <../../../examples/ExecutionPools/Discover/sub_proj2/__init__.py>`
  - :download:`sub_proj2/suites.py <../../../examples/ExecutionPools/Discover/sub_proj2/suites.py>`
  - :download:`sub_proj2/tasks.py <../../../examples/ExecutionPools/Discover/sub_proj2/tasks.py>`

test_plan.py
++++++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Discover/test_plan.py

sub_proj1/tasks.py
++++++++++++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Discover/sub_proj1/tasks.py

sub_proj2/tasks.py
++++++++++++++++++
.. literalinclude:: ../../../examples/ExecutionPools/Discover/sub_proj2/tasks.py