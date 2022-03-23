.. _Exotic:

Exotic features
***************

Report target decorator
-----------------------

The result of a particular run stores associated filepath
and line number information for each of the assertions,
optionally displayed also on the UI.
These, by default, point to the testcase-level of the call stack,
regardless of whether the assertion happens in another function.
Consider, for example, the below snippet.

.. code-block:: python
    ...
    def helper(result):
        result.equal(1, 1)

    @testsuite
    class Suite:
        @testcase
        def case(self, env, result):
            result.less(1, 2)
            helper(result)

When ``case`` is executed, ``result.equal`` will point to the line
where ``helper`` is called inside ``case``.
This behavior makes clear the actual testcase to which the assertion belongs to
and can be thought of as "marking" of testcases as assertions.

What if one prefers to get a pointer to the assertion itself consistently across
both suites and cases?
Testplan allows the user to turn off the marking at ``MultiTest`` level.
Let us extend the previous snippet.

.. code-block:: python
    ...
    multitest = Multitest(
        ...,
        suites=[Suite()],
        testcase_report_target=False,
    )

Running the multitest with above configuration makes the assertion in
``result.equal`` point to the line where it is called inside ``helper``
rather than to where ``helper`` is called inside ``case``.

Controlling the behavior at ``MultiTest`` level may be sufficient in most scenarios,
but it is a binary decision.
In case the pointer is best-placed elsewhere for some special cases, the underlying
:py:meth:`report_target <testplan.testing.multitest.result.report_target>` decorator can be leveraged.
Roughly speaking, :py:meth:`report_target <testplan.testing.multitest.result.report_target>`
is applied to all the testcases by default, and it pulls the pointer to testcase level.
Decorating functions further down the call chain makes each assertion
point to the nearest decorated.
Let us extend the snippet further.

.. code-block:: python
    @report_target
    def intermediary(result):
        helper(result)
    ...

    @testsuite
    class Suite:
        ...
        @testcase
        def case_b(self, env, result):
            intermediary(result)

Independent of whether ``testcase_report_target`` was passed as
``True`` or ``False`` to the ``MultiTest`` constructor, the ``result.equal`` assertion
in ``case_b`` will point to the call of ``helper`` inside ``intermediary``, since
it is the nearest "marked" function.
Note that behavior of assertions in ``case`` are not impacted
as ``intermediary`` is not called there.

The :ref:`examples <example_assertions_marking>` provide further guidance on
how the marking logic works in practice.
Switching between the default and non-default behavior at ``MultiTest`` level
gives further insight.
