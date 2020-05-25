Output
******

Testplan provides comprehensive test output styles made available from
the built-in test report exporters. These are the following:

.. _Output_Console:

Console
=======

Based on the verbosity specified with command line options or programmatically
(see the :ref:`downloadable example <example_test_output_console>` that demonstrates that),
the assertions/testcases/testsuites/Multitest level results will be printed on the console:

    * **Basic** assertions verbose output:

        .. image:: ../images/output/console/basic_assertions.png

    * **Table** assertions verbose output:

        .. image:: ../images/output/console/table_assertions.png

    * **Fix/Dict** match assertions verbose output:

        .. image:: ../images/output/console/fix_assertions.png

.. _Output_Browser:

Browser
=======

Command line option ``--ui`` can be used to start a local web server after
Testplan runs. Testplan will print a URL to console which can be used in a
browser (Chrome, Firefox or Edge) to view the Testplan report in the browser UI.
This exporter requires the ``install-testplan-ui`` script to have been run (see
:ref:`Install Testplan <install_testplan>` in the Getting Started section). If
this script hasn't been run the web server will start but the report won't load
in the browser.

    * **Basic** assertions Browser UI representation:

        .. image:: ../images/output/browser/basic_assertions.png

    * **Table** assertions Browser UI representation:

        .. image:: ../images/output/browser/table_assertions.png

    * **Fix/Dict** match assertions Browser UI represenation:

        .. image:: ../images/output/browser/fix_assertions.png

.. _Output_PDF:

PDF
===

PDF output concept is similar to console but it is used when persistent test evidence are needed.
Command line options ``--pdf`` and ``--pdf-style`` can be used to generate PDF reports but that
can also be done programmatically with ``pdf_path`` and ``pdf_style`` configuration options of Testplan
(most of our downloadable examples do that by default).

    * **Basic** assertions PDF representation:

        .. image:: ../images/output/pdf/basic_assertions.png

    * **Table** assertions PDF representation:

        .. image:: ../images/output/pdf/table_assertions.png

    * **Fix/Dict** match assertions PDF representation:

        .. image:: ../images/output/pdf/fix_assertions.png

    * **Matplot** assertions PDF representation:

        .. image:: ../images/output/pdf/matplot_assertions.png

.. _Output_XML:

XML
===

XML output can be generated per each MultiTest in a plan, and can be used as an alternative
format for persistent test evidence. To generate XML output, you can use ``--xml-dir`` and provide
a directory for XML files. The generated XML files will be in JUnit format:

.. code-block:: xml

    <testsuites>
      <testsuite tests="3" errors="0" name="AlphaSuite" package="Primary:AlphaSuite" hostname="hostname.example.com" failures="1" id="0">
        <testcase classname="Primary:AlphaSuite:test_equality_passing" name="test_equality_passing" time="0.138505"/>
        <testcase classname="Primary:AlphaSuite:test_equality_failing" name="test_equality_failing" time="0.001906">
          <failure message="failing equality" type="assertion"/>
        </testcase>
        <testcase classname="Primary:AlphaSuite:test_membership_passing" name="test_membership_passing" time="0.00184"/>
        <system-out/>
        <system-err/>
      </testsuite>
    </testsuites>

.. _Output_JSON:

JSON
====

A JSON file that fully represents the test data can be generated via ``--json`` command.
Testplan supports serialization / deserialization of test reports, meaning
the native report object can be deserialized from this JSON file as well.

Sample JSON output:

.. code-block:: python

  {"entries": [{
    "category": "multitest",
    "description": null,
    "entries": [{
      "category": "suite",
      "description": null,
      "entries": [{
        "description": null,
        "entries": [{
          "category": null,
          "description": "passing equality",
          "first": 1,
          "label": "==",
          "line_no": 54,
          "machine_time": "2018-02-05T15:16:40.951528+00:00",
          "meta_type": "assertion",
          "passed": True,
          "second": 1,
          "type": "Equal",
          "utc_time": "2018-02-05T15:16:40.951516+00:00"}
        ],
        "logs": [],
        "name": "passing_testcase_one",
        "status": "passed",
        "status_override": null,
        "tags": {},
        "tags_index": {},
        "timer": {
          "run": {
            "end": "2018-02-05T15:16:41.164086+00:00",
            "start": "2018-02-05T15:16:40.951456+00:00"}},
            "type": "TestCaseReport",
            "uid": "9b4467e2-668c-4764-942b-061ea58da0f0"
          },
        ...
        ],
        "logs": [],
        "name": "BetaSuite",
        "status": "passed",
        "status_override": null,
        "tags": {},
        "tags_index": {},
        "timer": {},
        "type": "TestGroupReport",
        "uid": "eeb87e19-ffcb-4710-8eeb-6daff89c46d9"}],
        "logs": [],
        "name": "MyMultitest",
        "status": "passed",
        "status_override": null,
        "tags": {},
        "tags_index": {},
        "timer": {},
        "type": "TestGroupReport",
        "uid": "bf44e942-c267-42b9-b379-5ec8c4c7878b"}
      ],
     "meta": {},
     "name": "Basic JSON Report Example",
     "status": "passed",
     "status_override": null,
     "tags_index": {},
     "timer": {
      "run": {
        "end": "2018-02-05T15:16:41.188904+00:00",
        "start": "2018-02-05T15:16:40.937402+00:00"
      }
    },
    uid": "5d541277-e0c4-43c6-941b-dea2c7d3259c"
  }

.. _styling_output:

Styles
======

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

.. _output_exporters:

.. include:: exporters.rst

