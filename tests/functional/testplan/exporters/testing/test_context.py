"""Test run_exporter and ExportContext."""

from testplan import TestplanMock
from testplan.exporters.testing import Exporter
from testplan.testing import multitest

EXPORT_MSG = "lorem ipsum"
EXCEPTION_MSG = "it is not your fault"


@multitest.testsuite
class Alpha:
    @multitest.testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, "equality description")

    @multitest.testcase
    def test_membership(self, env, result):
        result.contain(1, [1, 2, 3])


@multitest.testsuite
class Beta:
    @multitest.testcase
    def test_failure(self, env, result):
        result.equal(1, 2, "failing assertion")
        result.not_equal(5, 5)

    @multitest.testcase
    def test_error(self, env, result):
        raise Exception("foo")


class EchoExporter(Exporter):
    """Dummy exporter."""

    def __init__(self, name="Echo exporter", message=None):
        super(EchoExporter, self).__init__(name=name)
        self.message = message

    def export(self, source, export_context):
        return {"message": self.message}


class ParrotExporter(Exporter):
    """Repeats what the previous exporter said."""

    def export(self, source, export_context):
        if export_context.results:
            return list(export_context.results)[-1].result


class FailingExporter(Exporter):
    """This one is not so lucky."""

    def export(self, source, export_context):
        raise Exception(EXCEPTION_MSG)


def test_exception_getting_caught_in_context():
    plan = TestplanMock(name="plan", exporters=FailingExporter())

    mt = multitest.MultiTest(name="Primary", suites=[Alpha()])
    plan.add(mt)
    plan.run()

    assert plan.runnable.result.exporter_results[0].success == False
    assert EXCEPTION_MSG in plan.runnable.result.exporter_results[0].traceback


def test_exporter_can_access_previous_exports():
    plan = TestplanMock(
        name="plan",
        exporters=[
            EchoExporter(message=EXPORT_MSG),
            ParrotExporter(),
        ],
    )

    mt = multitest.MultiTest(name="Primary", suites=[Alpha()])
    plan.add(mt)
    plan.run()

    assert len(plan.runnable.result.exporter_results) == 2

    assert type(plan.runnable.exporters[0]) is EchoExporter
    assert type(plan.runnable.exporters[1]) is ParrotExporter

    assert plan.runnable.result.exporter_results[1].success == True
    assert (
        plan.runnable.result.exporter_results[1].result["message"]
        == EXPORT_MSG
    )
