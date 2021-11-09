import os
import sys
import atexit
import collections

from testplan import TestplanMock
from testplan.testing.multitest import MultiTest
from testplan.common.utils.comparison import compare

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

ModuleInfo = collections.namedtuple(
    "ModuleInfo",
    "template_path module_path "
    "original_value updated_value original_report updated_report",
)

TEST_SUITE_MODULES = [
    # A module in the same directory as the main script
    ModuleInfo(
        os.path.abspath(
            os.path.join(THIS_DIRECTORY, "basic_suite_template.txt")
        ),
        os.path.abspath(os.path.join(THIS_DIRECTORY, "basic_suite.py")),
        "0",
        "1",
        [
            {
                "type": "Equal",
                "meta_type": "assertion",
                "category": "DEFAULT",
                "description": "Equal Assertion",
                "label": "==",
                "passed": False,
                "flag": "DEFAULT",
                "first": 1,
                "second": 0,
                "type_expected": "int",
                "type_actual": "int",
            }
        ],
        [
            {
                "type": "Equal",
                "meta_type": "assertion",
                "category": "DEFAULT",
                "description": "Equal Assertion",
                "label": "==",
                "passed": True,
                "flag": "DEFAULT",
                "first": 1,
                "second": 1,
                "type_expected": "int",
                "type_actual": "int",
            }
        ],
    ),
    # A module in a package which is in the same directory as the main script
    ModuleInfo(
        os.path.abspath(
            os.path.join(THIS_DIRECTORY, "tasks", "inner_suite_template.txt")
        ),
        os.path.abspath(
            os.path.join(THIS_DIRECTORY, "tasks", "inner_suite.py")
        ),
        "",
        (
            "    @testcase\n"
            "    def another_case(self, env, result):\n"
            '        result.false(False, description="Fallacy Assertion")\n'
        ),
        [
            {
                "type": "IsTrue",
                "meta_type": "assertion",
                "category": "DEFAULT",
                "description": "Truth Assertion",
                "passed": True,
                "flag": "DEFAULT",
                "expr": True,
            }
        ],
        [
            {
                "type": "IsTrue",
                "meta_type": "assertion",
                "category": "DEFAULT",
                "description": "Truth Assertion",
                "passed": True,
                "flag": "DEFAULT",
                "expr": True,
            },
            {
                "type": "IsFalse",
                "meta_type": "assertion",
                "category": "DEFAULT",
                "description": "Fallacy Assertion",
                "passed": True,
                "flag": "DEFAULT",
                "expr": False,
            },
        ],
    ),
    # A module outside of the current directory that places the main script
    ModuleInfo(
        os.path.abspath(
            os.path.join(
                THIS_DIRECTORY,
                os.pardir,
                "extra_deps",
                "extra_suite_template.txt",
            )
        ),
        os.path.abspath(
            os.path.join(
                THIS_DIRECTORY, os.pardir, "extra_deps", "extra_suite.py"
            )
        ),
        "fail",
        "log",
        [
            {
                "type": "Fail",
                "meta_type": "assertion",
                "category": "DEFAULT",
                "description": "Write a message into report",
                "passed": False,
                "flag": "DEFAULT",
            }
        ],
        [
            {
                "type": "Log",
                "meta_type": "entry",
                "category": "DEFAULT",
                "description": "Write a message into report",
                "message": "Write a message into report",
                "flag": "DEFAULT",
            }
        ],
    ),
]


def _compare_reports(expected_reports, actual_reports, ignore=None):
    # Compare the content of testcase reports
    assert len(expected_reports) == len(actual_reports)
    for expected_report, actual_report in zip(
        expected_reports, actual_reports
    ):
        assert len(expected_report) == len(actual_report)
        for expected_entry, actual_entry in zip(
            expected_report, actual_report
        ):
            assert (
                compare(expected_entry, actual_entry, ignore=ignore)[0] is True
            )


def main():
    # Create module files that contain test suite definition
    for module_info in TEST_SUITE_MODULES:
        with open(module_info.template_path, "r") as fp_r, open(
            module_info.module_path, "w"
        ) as fp_w:
            fp_w.write(fp_r.read().format(VALUE=module_info.original_value))
        # module files will be removed after testing
        atexit.register(os.remove, module_info.module_path)

    # Import 3 test suites
    extra_path = os.path.abspath(os.path.join(THIS_DIRECTORY, os.pardir))
    sys.path.insert(0, extra_path)
    try:
        import basic_suite
        from tasks import inner_suite
        from extra_deps import extra_suite
    finally:
        sys.path.remove(extra_path)

    # Create an interactive Testplan
    plan = TestplanMock(
        name="MyPlan",
        interactive_port=0,
        interactive_block=False,
        extra_deps=[extra_suite],
    )

    # Add 2 MultiTest instances and trigger run of interactive executioner
    plan.add(MultiTest(name="BasicTest", suites=[basic_suite.BasicSuite()]))
    plan.add(MultiTest(name="InnerTest", suites=[inner_suite.InnerSuite()]))
    plan.add(MultiTest(name="ExtraTest", suites=[extra_suite.ExtraSuite()]))
    plan.run()

    # Run tests
    plan.i.run_all_tests()

    # Check reports
    _compare_reports(
        expected_reports=[
            module_info.original_report for module_info in TEST_SUITE_MODULES
        ],
        actual_reports=[
            [
                plan.i.test_case_report(
                    test_uid="BasicTest",
                    suite_uid="BasicSuite",
                    case_uid="basic_case",
                    serialized=True,
                )["entries"][0]["entries"][0]["entries"][0],
            ],
            [
                plan.i.test_case_report(
                    test_uid="InnerTest",
                    suite_uid="InnerSuite",
                    case_uid="basic_case",
                    serialized=True,
                )["entries"][0]["entries"][0]["entries"][0],
            ],
            [
                plan.i.test_case_report(
                    test_uid="ExtraTest",
                    suite_uid="ExtraSuite",
                    case_uid="basic_case",
                    serialized=True,
                )["entries"][0]["entries"][0]["entries"][0],
            ],
        ],
        ignore=["file_path", "line_no", "machine_time", "utc_time"],
    )
    assert plan.i.report.passed is False

    # Apply code changes, two testcase changed and one newly added
    for module_info in TEST_SUITE_MODULES:
        with open(module_info.template_path, "r") as fp_r, open(
            module_info.module_path, "w"
        ) as fp_w:
            fp_w.write(fp_r.read().format(VALUE=module_info.updated_value))

    # Reload code from changed files and uodate report
    plan.i.reload()
    plan.i.reload_report()

    # Run tests again
    plan.i.run_all_tests()

    # Check reports
    _compare_reports(
        expected_reports=[
            module_info.updated_report for module_info in TEST_SUITE_MODULES
        ],
        actual_reports=[
            [
                plan.i.test_case_report(
                    test_uid="BasicTest",
                    suite_uid="BasicSuite",
                    case_uid="basic_case",
                    serialized=True,
                )["entries"][0]["entries"][0]["entries"][0],
            ],
            [
                plan.i.test_case_report(
                    test_uid="InnerTest",
                    suite_uid="InnerSuite",
                    case_uid="basic_case",
                    serialized=True,
                )["entries"][0]["entries"][0]["entries"][0],
                plan.i.test_case_report(
                    test_uid="InnerTest",
                    suite_uid="InnerSuite",
                    case_uid="another_case",
                    serialized=True,
                )["entries"][0]["entries"][0]["entries"][0],
            ],
            [
                plan.i.test_case_report(
                    test_uid="ExtraTest",
                    suite_uid="ExtraSuite",
                    case_uid="basic_case",
                    serialized=True,
                )["entries"][0]["entries"][0]["entries"][0],
            ],
        ],
        ignore=["file_path", "line_no", "machine_time", "utc_time"],
    )
    assert plan.i.report.passed is True


if __name__ == "__main__":
    main()
