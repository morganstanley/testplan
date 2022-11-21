.. _Trace:

Tracing Impacted Tests
**********************

Introduction
============

There are certain circumstances that one need to pay extra attentions to changes
during software development process. Obviously such change could possibly affect
some tests and make them fail inside the CI pipelines. It would be quite helpful
for the developers to get a list of impacted tests given such change, to e.g.
either suggests a list of tests that should be checked before going into production,
or to help them quickly narrow down the range of tests that should be fixed. Here
change refers to a set of file paths paired with a set of line numbers for Testplan
to keep an eye on when executing the tests. This change, due to its possibly big size,
should be encoded in JSON format and stored in a readable file.

.. note::

    Currently this tracing impacted tests feature only works on Testplan MultiTests.
    Due to certain implementation limit, this feature currently doesn't work well
    with testcase parallel execution, and no impact tests data will be collected
    for parallel executed testcases.

Usage
=====

To use this feature, you may run your testplan with extra flag "--watch-lines"
following by the path to a JSON file containing changed files and lines:

.. code-block:: bash

    $ echo { \"my_module.py\": [1, 2, 3, 4] } > changed_lines.json
    $ python test_plan.py --watch-lines changed_lines.json

Or maybe you want to watch the whole file:

.. code-block:: bash

    $ echo { \"my_module.py\": "*", \"my_other_module.py\": "*" } > changed_lines.json
    $ python test_plan.py --watch-lines changed_lines.json

By default this list of impacted tests will be printed to the standard output,
but you can certainly specify the output file with "--output-impacted-tests":

.. code-block:: bash

    $ # assuming we already got a valid "changed_lines.json"
    $ python test_plan.py \
    $   --watch-lines changed_lines.json \
    $   --output-impacted-tests tests_need_attention

The output tests will be in Testplan filtering pattern.
