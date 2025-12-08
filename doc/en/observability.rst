.. _Observability:

Observability
*************

Testplan provides built-in observability through OpenTelemetry tracing, allowing you to monitor
and analyze test execution. This feature enables you to:

  * Track test execution flow and timing
  * Debug performance bottlenecks
  * Monitor test execution

Overview
========

The observability feature integrates OpenTelemetry to create spans for various levels of test execution:

  1. **Testplan level**: Top-level span for the entire test plan
  2. **Test level**: Spans for individual test runnables (MultiTest, PyTest, GTest, etc.)
  3. **Testsuite level**: Spans for test suites (MultiTest only)
  4. **Testcase level**: Spans for individual test cases (MultiTest only)

For test types other than MultiTest (such as PyTest, GTest, JUnit), only the entire test execution
is traced as a single span, without breaking down into individual suites or cases.

Each span captures timing information, attributes, and status (pass/fail), allowing you to visualize
the complete test execution in your observability platform.

Configuration
-------------

Environment Variables
+++++++++++++++++++++

To enable OpenTelemetry tracing, set the following environment variables:

**Required Variables:**

.. code-block:: bash

    # OTLP exporter endpoint
    export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://your-otlp-endpoint:4317

    # Headers for the endpoint
    export OTEL_EXPORTER_OTLP_HEADERS="header1=value1"

    # TLS certificates for gRPC connection
    export OTEL_EXPORTER_OTLP_CERTIFICATE=/path/to/ca-cert.pem
    export OTEL_EXPORTER_OTLP_CLIENT_KEY=/path/to/client-key.pem
    export OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE=/path/to/client-cert.pem

    # Resource attributes (key-value format)
    export OTEL_RESOURCE_ATTRIBUTES="service.name=my-testplan,environment=staging,team=qa"

**Optional Variables:**

.. code-block:: bash
    # Batch span processor delay in milliseconds (default: 200)
    export OTEL_BSP_SCHEDULE_DELAY=500

Then, use the ``--otel-trace`` command line flag:

.. code-block:: bash

    # Enable tracing with the flag
    python my_testplan.py --otel-trace <LEVEL> [Test|TestSuite|TestCase]

Where ``<LEVEL>`` can be:
    * ``Test``: Trace at the Testplan and Test levels
    * ``TestSuite``: Trace at the Testplan, Test, and Testsuite levels
    * ``TestCase``: Trace at all levels including Testcase

You can also set the tracing level programmatically in your test plan definition:

.. code-block:: python

    from testplan import test_plan

    @test_plan(name="MyTestPlan", otel_traces="TestCase")
    def main(plan):
        # Your test plan definition here
        pass

Trace Context Propagation
++++++++++++++++++++++++++

When you need to integrate Testplan traces into an existing distributed trace, use the ``--otel-traceparent`` flag
to specify the parent trace context in W3C Trace Context format:

.. code-block:: bash

    # Link Testplan execution to an existing trace
    python my_testplan.py --otel-trace TestCase --otel-traceparent "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"

The traceparent format is: ``version-trace_id-parent_span_id-trace_flags``

This allows your Testplan execution to appear as a child span in your broader system trace, enabling
end-to-end observability across multiple test executions. A common use case is to start
a parent trace and have multiple Testplan runs execute in parallel as child spans under that trace.
You can generate a traceparent with a script like the following:

.. code-block:: python

    # start_trace.py
    import sys
    from testplan.common.utils.observability import tracing

    def main():
        tracing._setup()
        with tracing.span("Trace Start"):
            tracing._inject_root_context()
            print(tracing._get_traceparent())

    if __name__ == "__main__":
        sys.exit(main())

Then pass the output to multiple parallel Testplan runs:

.. code-block:: bash

    # Start the parent trace and capture the traceparent
    TRACEPARENT=$(python start_trace.py | tail -n 1)
    
    # Launch multiple testplan runs in parallel under the same parent trace
    python testplan1.py --otel-trace TestCase --otel-traceparent "$TRACEPARENT" &
    python testplan2.py --otel-trace TestCase --otel-traceparent "$TRACEPARENT" &
    python testplan3.py --otel-trace TestCase --otel-traceparent "$TRACEPARENT" &
    wait

Tracing
-----------------

The tracing hierarchy follows the test structure:

.. code-block:: text

    Testplan (root span)
    ├── MultiTest
    │   ├── TestSuite1
    │   │   ├── testcase_1
    │   │   ├── testcase_2
    │   │   └── testcase_3
    │   └── TestSuite2
    │       ├── testcase_4
    │       └── testcase_5
    ├── PyTest
    └── GTest

Each span includes:

  * **Name**: The name of the test/suite/case
  * **Attributes**: Metadata like test level, status, etc.
  * **Status**: Pass/error based on test results
  * **Timing**: Start and end timestamps

Manual Span Creation
--------------------

For custom instrumentation within your tests, you can manually create spans:

Context Manager Style
+++++++++++++++++++++

.. code-block:: python

    from testplan.common.utils.observability import tracing
    
    @testcase
    def my_test(self, env, result):
        with tracing.span("database_query", db="postgres", query="SELECT"):
            # Your code here
            result.true(perform_database_query())

Start/End Style
+++++++++++++++

.. code-block:: python

    @testcase
    def my_test(self, env, result):
        # Start a span
        span = tracing.start_span(
            "complex_operation",
            operation="data_processing",
            record_count=1000
        )
        
        try:
            result.true(process_data())
        finally:
            # End the span
            tracing.end_span("complex_operation")

Setting Span Attributes
++++++++++++++++++++++++

.. code-block:: python

    @testcase
    def my_test(self, env, result):
        with tracing.span("api_call") as span:
            response = call_api()
            
            # Add custom attributes to the span
            tracing.set_span_attrs(
                span=span,
                status_code=response.status_code,
                response_time_ms=response.elapsed.total_seconds() * 1000
            )
            
            result.equal(response.status_code, 200)

Marking Spans as Failed
++++++++++++++++++++++++

.. code-block:: python

    @testcase
    def my_test(self, env, result):
        with tracing.span("validation") as span:
            data = fetch_data()
            
            if not validate(data):
                tracing.set_span_as_failed(
                    span=span,
                    description="Data validation failed"
                )
                result.fail("Invalid data")


See :ref:`example here <example_observability>`.

Distributed Tracing
-------------------

When running tests in distributed environments (e.g., with :ref:`pools <Pools>`), tracing
context can be propagated across process boundaries. For remote pools such as RemotePool, 
you either need to ensure that the environment variables are set on the remote or explicitly pass the OpenTelemetry environment variables to the pool workers:

.. code-block:: python

    import os
    from testplan import test_plan
    from testplan.runners.pools import RemotePool
    from testplan.runners.pools.tasks import Task
    
    @test_plan(name="DistributedTracing")
    def main(plan):
        # Collect OTEL environment variables to pass to workers
        otel_keys = [
            'OTEL_RESOURCE_ATTRIBUTES',
            'OTEL_EXPORTER_OTLP_HEADERS',
            'OTEL_EXPORTER_OTLP_TRACES_ENDPOINT',
            'OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE',
            'OTEL_EXPORTER_OTLP_CLIENT_KEY',
            'OTEL_EXPORTER_OTLP_CERTIFICATE',
        ]
        env_dict = {k: os.environ.get(k) for k in otel_keys if os.environ.get(k)}
        
        # Add a pool with OTEL environment variables
        pool = RemotePool(
            name="MyPool",
            size=4,
            env=env_dict  # Pass OTEL environment to workers
        )
        plan.add_resource(pool)
        
        # Tasks will inherit the root trace context
        for idx in range(10):
            task = Task(
                target='make_multitest',
                module='tasks',
                path='.'
            )
            plan.schedule(task, resource='MyPool')

The root trace context is automatically injected into worker processes. When the environment
variables are configured correctly, trace export will occur normally and trace propagation
will continue as expected across the distributed test execution.