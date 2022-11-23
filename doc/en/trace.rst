.. _Trace:

Tracing Impacted Tests
**********************

Introduction
============

This feature needs to take in a JSON file containing Python file names and lines
numbers, and will report a list of tests that executes through those lines during
Testplan execution, in the format of Testplan filtering pattern. It would be useful
if the developers want to get a set of tests impacted by some specific change.

.. note::

    Currently this tracing tests feature will only work on Testplan MultiTests.
    Due to certain implementation limit, this feature currently doesn't work well
    with testcase parallel execution, and no impact tests data will be collected
    for parallel executed testcases. This feature will be automatically switched
    off when Testplan running in interactive mode as well.

Usage
=====

To use this feature, you may run your testplan with extra flag ``--trace-tests``
following by the path to a JSON file containing changed files and lines:

.. code-block:: bash

    $ echo { \"my_module.py\": [1, 2, 3, 4] } > changed_lines.json
    $ python test_plan.py --trace-tests changed_lines.json

Or maybe you want to trace the whole file:

.. code-block:: bash

    $ echo { \"my_module.py\": \"*\", \"my_other_module.py\": \"*\" } > changed_lines.json
    $ python test_plan.py --trace-tests changed_lines.json

By default this list of impacted tests will be printed to the standard output,
but you can certainly specify the output file with ``--trace-tests-output``:

.. code-block:: bash

    $ # assuming we already have a valid "changed_lines.json"
    $ python test_plan.py \
    $   --trace-tests changed_lines.json \
    $   --trace-tests-output tests_need_attention

The output tests will be in Testplan filtering pattern.
