Customization
=============

.. _Custom_Exporter:

Custom Exporter
---------------

You can define your exporters by inheriting from the base exporter class and use
them by passing them to ``@test_plan`` decorator via ``exporters`` list.

Custom export functionality should be implemented within ``export`` method.

Each exporter in the ``exporters`` list will get a fresh copy of the original
source (e.g. :py:class:`report <testplan.report.testing.base.TestReport>`).

.. code-block:: python

    from testplan.exporters.testing import Exporter


    class CustomExporter(Exporter):

        def export(self, source):
            # Custom logic goes here
            ...

    @test_plan(name='SamplePlan', exporters=[CustomExporter(...)])
    def main(plan):
        ...

Examples for custom exporter implementation can be seen :ref:`here <example_test_output_exporters_custom>`.


.. _Styling_Output:

Output Styles
-------------

Certain output processors (e.g. stdout, PDF) make use of the
generic :py:class:`style objects <testplan.report.testing.styles.Style>` for
formatting.

A style object can be initialized with 2 arguments, corresponding display levels for
passing and failing tests. These levels should be one of
:py:class:`StyleEnum <testplan.report.testing.styles.StyleEnum>` values
(e.g. ``StyleEnum.CASE``) or their lowercase string representations (e.g. ``'case'``)

.. code-block:: python

    from testplan.report.testing.styles import Style, StyleEnum

    # These style declarations are equivalent.
    style_1_a = Style(passing=StyleEnum.TEST, failing=StyleEnum.CASE)
    style_1_b = Style(passing='test', failing='case')


Style levels are incremental, going from the least verbose to the most verbose:

.. code-block:: python

    RESULT = 0  #  Plan level output, the least verbose
    TEST = 1
    SUITE = 2
    CASE = 3
    ASSERTION = 4
    ASSERTION_DETAIL = 5  #  Assertion detail level output, the most verbose


This means when we have a declaration like ``Style(passing=StyleEnum.TESTCASE, failing=StyleEnum.TESTCASE)``
the output will include information starting from Plan level down to testcase method level,
but it will not include any assertion information.

Here's a simple schema that highlights minimum required styling level for viewing related test information:

.. code-block:: bash

    Testplan -> StyleEnum.RESULT
    |
    +---- MultiTest 1  -> StyleEnum.TEST
    |     |
    |     +---- Suite 1  -> StyleEnum.SUITE
    |     |     |
    |     |     +--- testcase_method_1  -> StyleEnum.CASE
    |     |     |    |
    |     |     |    +---- assertion statement  -> StyleEnum.ASSERTION
    |     |     |    +---- assertion statement
    |     |     |          ( ... assertion details ...)  -> StyleEnum.ASSERTION_DETAIL
    |     |     |
    |     |     +---- testcase_method_2
    |     |     +---- testcase_method_3
    |     |
    |     +---- Suite 2
    |           ...
    +---- MultiTest 2
          ...


Here is a sample usage of styling objects:

.. code-block:: python

  from testplan.report.testing.styles import Style, StyleEnum

  @test_plan(
      name='SamplePlan',
      # On console output configuration
      # Display down to testcase level for passing tests
      # Display all details for failing tests
      stdout_style=Style(
        passing=StyleEnum.CASE,
        failing=StyleEnum.ASSERTION_DETAIL
      ),
      pdf_path='my-report.pdf',
      # PDF report configuration
      # Display down to basic assertion level for passing tests
      # Display all details for failing tests
      pdf_style=Style(
          passing=StyleEnum.ASSERTION,
          failing=StyleEnum.ASSERTION_DETAIL
      )
  )
  def main(plan):
    ...

