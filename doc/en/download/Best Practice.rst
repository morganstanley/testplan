.. _example_best_practice:

Best Practice
*************

.. _example_common_utilities:

Helper Utilities
================

Testplan provides helper functions and a predefined testsuite that make it
easy for the user to add common testplan execution infomation - such as
env var, pwd, log file, driver metadata - to the test report.

DriverLogCollector
------------------
You can specify your custom log collector using :py:class:`~testplan.common.utils.helper.DriverLogCollector`.
It will attach the specified log files to the report for each driver.
Example:
    .. code-block:: python

      from testplan.common.utils import helper

      log_collector = helper.DriverLogCollector(
          name="custom_log_collector",
          file_pattern=["*.log"],
          description="Driver log files",
          ignore="not_important.log",
          recursive=True,
          failure_only=False,
      )
      log_collector(env, result)

Required files:
    - :download:`test_plan.py <../../../examples/Best Practice/Common Utilities/test_plan.py>`

test_plan.py
++++++++++++
.. literalinclude:: ../../../examples/Best Practice/Common Utilities/test_plan.py