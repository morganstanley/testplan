Assertions
**********

.. _example_assertions:

Basic
-----

.. _example_assertions_basic:

Required files:
  - :download:`test_plan_basic.py <../../../examples/Assertions/Basic/test_plan_basic.py>`

test_plan_basic.py
++++++++++++++++++
.. literalinclude:: ../../../examples/Assertions/Basic/test_plan_basic.py

Required files:
  - :download:`test_plan_group.py <../../../examples/Assertions/Basic/test_plan_group.py>`

test_plan_group.py
++++++++++++++++++
.. literalinclude:: ../../../examples/Assertions/Basic/test_plan_group.py

Required files:
  - :download:`test_plan_exception.py <../../../examples/Assertions/Basic/test_plan_exception.py>`

test_plan_exception.py
++++++++++++++++++++++
.. literalinclude:: ../../../examples/Assertions/Basic/test_plan_exception.py

Required files:
  - :download:`test_plan_dict.py <../../../examples/Assertions/Basic/test_plan_dict.py>`

test_plan_dict.py
+++++++++++++++++
.. literalinclude:: ../../../examples/Assertions/Basic/test_plan_dict.py

Required files:
  - :download:`test_plan_fix.py <../../../examples/Assertions/Basic/test_plan_fix.py>`

test_plan_fix.py
++++++++++++++++
.. literalinclude:: ../../../examples/Assertions/Basic/test_plan_fix.py

Required files:
  - :download:`test_plan_regex.py <../../../examples/Assertions/Basic/test_plan_regex.py>`

test_plan_regex.py
++++++++++++++++++
.. literalinclude:: ../../../examples/Assertions/Basic/test_plan_regex.py

Required files:
  - :download:`test_plan_table.py <../../../examples/Assertions/Basic/test_plan_table.py>`

test_plan_table.py
++++++++++++++++++
.. literalinclude:: ../../../examples/Assertions/Basic/test_plan_table.py

Required files:
  - :download:`test_plan_xml.py <../../../examples/Assertions/Basic/test_plan_xml.py>`

test_plan_xml.py
++++++++++++++++
.. literalinclude:: ../../../examples/Assertions/Basic/test_plan_xml.py

.. _example_assertions_custom_style:

Required files:
  - :download:`test_plan_custom_style.py <../../../examples/Assertions/Basic/test_plan_custom_style.py>`

test_plan_custom_style.py
+++++++++++++++++++++++++
.. literalinclude:: ../../../examples/Assertions/Basic/test_plan_custom_style.py


Summarization
-------------

.. _example_assertions_summary:

Required files:
  - :download:`test_plan.py <../../../examples/Assertions/Summary/test_plan.py>`

test_plan.py
++++++++++++
.. literalinclude:: ../../../examples/Assertions/Summary/test_plan.py


Plotly
------

.. _example_assertions_plotly:

Required files:
  - :download:`test_plan.py <../../../examples/Assertions/Plotly/test_plan.py>`

test_plan.py
++++++++++++
.. literalinclude:: ../../../examples/Assertions/Plotly/test_plan.py


Marking
-------
These examples demonstrate the usage of the `mark_group` decorator
which allows modifying the default line number and filepath of assertions in the report.
It does so by re-pointing both to line number and filepath information of the call stack
that is marked and closest to the actual assertion in scope.
For example, let us consider a call chain where a particular testcase calls an intermediary
that in turn calls a utility function holding the assertion.
By default, the line number and filepath of the entry would point to the assertion.
If the marking decorator is applied to the intermediary,
then it would point to the call of the utility.
Finally, if the marking is applied to both the intermediary and the utility,
then the entry would once again reference the assertion as the utility is the closest
mark "pulling" the pointer.

.. _example_assertions_marking:

Required files:
  - :download:`test_plan.py <../../../examples/Assertions/Marking/test_plan_linear.py>`

test_plan_linear.py
+++++++++++++++++++
.. literalinclude:: ../../../examples/Assertions/Marking/test_plan_linear.py

Required files:
  - :download:`test_plan.py <../../../examples/Assertions/Marking/test_plan_non_linear.py>`

test_plan_non_linear.py
+++++++++++++++++++++++
.. literalinclude:: ../../../examples/Assertions/Marking/test_plan_non_linear.py
