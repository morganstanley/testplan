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

.. code-block:: json

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

Exporters
=========

At the end of a test run Testplan creates a
:py:class:`report <testplan.report.testing.base.TestReport>` object, which is
used by exporters to output the test data to different targets.

Built-in
--------

PDF
+++

Testplan uses `Reportlab <http://www.reportlab.com/opensource/>`_ to generate
test reports in PDF format. The simplest way to enable this functionality is to
pass ``--pdf-path`` comand line argument:

.. code-block:: bash

    $ ./test_plan.py --pdf-path my-report.pdf
        [MultiTest] -> Pass
    [Testplan] -> Pass
    PDF generated at mypdf.pdf


It is also possible to use programmatic declaration for PDF report generation
as well:

.. code-block:: python

    @test_plan(name='SamplePlan', pdf_path='my-report.pdf'))
    def main(plan):
      # Testplan implicitly creates PDF exporter if we just pass `pdf_path`
      ...

A more explicit usage is to initialize a PDF exporter directly:

.. code-block:: python

    from testplan.exporters.testing import PDFExporter

    @test_plan(
      name='SamplePlan',
      exporters=[
          PDFExporter(pdf_path='my-report.pdf')
      ]
    )
    def main(plan):
    ...


Examples for PDF report generation can be seen :ref:`here <example_test_output_exporters_pdf>`.

PDF reports can contain different levels of detail, configured via styling
options. These options can be specified:

    * via command line:

        .. code-block:: bash

          $ ./test_plan.py --pdf-path my-report.pdf --pdf-style extended-summary

    * programmatically:

        .. code-block:: python

          from testplan.report.testing.styles import Style, StyleEnum

          @test_plan(
              name='SamplePlan',
              pdf_path='my-report.pdf',
              pdf_style=Style(
                  passing=StyleEnum.ASSERTION,
                  failing=StyleEnum.ASSERTION_DETAIL
              )
          ))
          def main(plan):
            ...

Read more about output styles :ref:`here <styling_output>`.


Tag filtered PDFs
+++++++++++++++++

If a plan has a very large number of tests, it may be better to generate
multiple PDF reports (filtered by tags), rather a single report.

Testplan provides such functionality via tag filtered PDF generation, which can
be enabled by ``--report-tags`` and ``--report-tags-all`` arguments:

Example tagger testsuite and testcase:

.. code-block:: python

    @testsuite(tags='alpha')
    class SampleTestAlpha(object):

        @testcase(tags='server')
        def test_method_1(self, env, result):
            ...

        @testcase(tags='database')
        def test_method_2(self, env, result):
            ...

        @testcase(tags=('server', 'client'))
        def test_method_3(self, env, result):
            ...


The command below will generate 2 PDFs, first one will contain test results from
tests tagged with ``database``, second one will contain the results from tests
tagged with ``server`` OR ``client``

A new PDF will be generated for each ``--report-tags``/``--report-tags-all``
argument.

.. code-block:: bash

    $ ./test_plan.py --report-dir ./reports --report-tags database --report-tags server client


Equivalent programmatic declaration for the same reports would be:

.. code-block:: python

    @test_plan(
      name='SamplePlan',
      report_dir='reports'
      report_tags=[
          'database',
          ('server', 'client')
      ]
    ))
    def main(plan):
        # Testplan implicitly creates Tag Filtered PDF exporter if we pass
        # the `report_tags` / `report_tags_all` arguments.
        ...


A more explicit usage is to initialize a Tag Filtered PDF exporter directly:

.. code-block:: python

    from testplan.exporters.testing import TagFilteredPDFExporter

    @test_plan(
        name='SamplePlan',
        exporters=[
            TagFiltered(
                report_dir='reports',
                report_tags=[
                    'database',
                    ('server', 'client')
                ]
            )
        ]
    )
    def main(plan):
       ...


Examples for Tag filtered PDF report generation can be seen :ref:`here <example_test_output_exporters_pdf>`.


XML
+++

Testplan supports XML exports compatible with the JUnit format. It is possible
to generate an XML file per each MultiTest in your plan.

The simplest way to enable this functionality is to use ``--xml-dir`` argument:

.. code-block:: bash

    $ ./test_plan.py --xml-dir /path/to/xml-dir

It is also possible to use programmatic declaration for XML generation as well:

.. code-block:: python

    @test_plan(name='SamplePlan', xml_dir='/path/to/xml-dir'))
    def main(plan):
        # Testplan implicitly creates XML exporter if we just pass `xml_dir`
        ...

A more explicit usage is to initialize an XML exporter directly.

.. code-block:: python

    from testplan.exporters.testing import XMLExporter

    @test_plan(
        name='SamplePlan',
        exporters=[
            XMLExporter(xml_dir='/path/to/xml-dir')
        ]
    )
    def main(plan):
      ...


Examples for XML report generation can be seen :ref:`here <example_test_output_exporters_xml>`.


JSON
++++

Testplan reports support JSON serialization / deserialization, meaning that
we can store the report as a JSON file and then load it back into the memory
to generate other kinds of output (e.g. PDF, XML or any custom export target).


A JSON report can be generated via ``--json`` argument:


.. code-block:: bash

  $ ./test_plan.py --json /path/to/json


Same result can be achieved by programmatic declaration as well:

.. code-block:: python

    @test_plan(name='Sample Plan', json_path='/path/to/json'))
    def main(plan):
        # Testplan implicitly creates JSON exporter if we just pass `json_path`
        ...

A more explicit usage is to initialize a JSON exporter directly:

.. code-block:: python

    from testplan.exporters.testing import JSONExporter

    @test_plan(
        name='Sample Plan',
        exporters=[
            JSONExporter(json_path='/path/to/json')
        ]
    )
    def main(plan):
        ...

Examples for JSON report generation can be seen :ref:`here <example_test_output_exporters_json>`.


Custom
------

You can define your exporters by inheriting from the base exporter class and use
them by passing them to ``@test_plan`` decorator via ``exporters`` list.

Custom export functionality should be implemented within ``export`` method.

Each exporter in the ``exporters`` list will get a fresh copy of the original
source (e.g. :py:class:`report <testplan.report.testing.base.TestReport>`).

.. code-block:: python

    from testplan.exporters.testing import Exporter


    class CustomExporter(Exporter):

        def export(self, source):
            ... Custom logic goes here ...

    @test_plan(name='SamplePlan', exporters=[CustomExporter(...)]))
    def main(plan):
        ...

Examples for custom exporter implementation can be seen :ref:`here <example_test_output_exporters_custom>`.
