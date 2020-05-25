Exporters
=========

At the end of a test run Testplan creates a
:py:class:`~testplan.report.testing.base.TestReport` object, which is used by
exporters to output the test data to different targets.

Built-in
--------

PDF
+++

Testplan uses `Reportlab <http://www.reportlab.com/opensource/>`_ to generate
test reports in PDF format. The simplest way to enable this functionality is to
pass ``--pdf`` comand line argument:

.. code-block:: bash

    $ ./test_plan.py --pdf my-report.pdf
        [MultiTest] -> Pass
    [Testplan] -> Pass
    PDF generated at mypdf.pdf


It is also possible to use programmatic declaration for PDF report generation
as well:

.. code-block:: python

    @test_plan(name='SamplePlan', pdf_path='my-report.pdf')
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

            $ ./test_plan.py --pdf my-report.pdf --pdf-style extended-summary

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
            )
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
    )
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

The simplest way to enable this functionality is to use ``--xml`` argument:

.. code-block:: bash

    $ ./test_plan.py --xml /path/to/xml-dir

It is also possible to use programmatic declaration for XML generation as well:

.. code-block:: python

    @test_plan(name='SamplePlan', xml_dir='/path/to/xml-dir')
    def main(plan):
        # Testplan implicitly creates XML exporter if we just pass `xml_dir`
        ...

A more explicit usage is to initialize a XML exporter directly.

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

    @test_plan(name='Sample Plan', json_path='/path/to/json')
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


WebServer
+++++++++

The WebServer exporter stores the report locally as a JSON file and then starts
a web server. You can start the web server via ``--ui`` arg. The port number
can be specified after the arg if a specific port is needed:

.. code-block:: bash

    $ ./test_plan.py --ui 12345


If defining programmatically, it is recommended to place this exporter last in
the list. This exporter will cause Testplan to block after all the exporters
have been run. It is recommended to place this exporter last in the list, if
declaring programmatically, as other exporters might also have post exporter
steps to be completed (e.g. PDF might be opened in the browser using
``--browse``).

.. code-block:: python

    from testplan.exporters.testing import WebServerExporter

    @test_plan(
        name='Sample Plan',
        exporters=[
            WebServerExporter(ui_port=12345)
        ]
    )
    def main(plan):
        ...

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
            # Custom logic goes here
            ...

    @test_plan(name='SamplePlan', exporters=[CustomExporter(...)])
    def main(plan):
        ...

Examples for custom exporter implementation can be seen :ref:`here <example_test_output_exporters_custom>`.
