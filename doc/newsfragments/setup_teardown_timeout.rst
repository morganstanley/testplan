* ``setup`` and ``teardown`` methods in test suites are timeout configurable to avoid program from hanging.

    .. code-block:: python

        from testplan.testing.multitest.suite import timeout

        @testsuite
        class MySuite(object):

            @timeout(300)
            def setup(self, env, result):
                ...

            @testcase(timeout=120)
            def test_example(self, env, result):
                ...

            @timeout(60)
            def teardown(self, env, result):
                ...
