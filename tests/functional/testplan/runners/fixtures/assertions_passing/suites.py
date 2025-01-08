"""Test Multitest - Test Suite - Result - Test Report - Exporter integration"""
import os
import re
import tempfile
from collections import OrderedDict

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan.common.utils import comparison as cmp, testing as test_utils


def always_true(obj):
    return True


@testsuite
class MySuite:
    @testcase
    def test_log(self, env, result):
        result.log("hello world")
        result.log("hello python", description="log description")

    @testcase
    def test_log_code(self, env, result):
        result.log_code(
            """
            #include<stdio.h>

            int main()
            {
                return 0
            }
            """,
            language="c",
            description="C codelog example",
        )

        result.log_code(
            """
            import os
            print(os.uname())
            """,
            language="python",
            description="Python codelog example",
        )

    @testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, "equality description")
        result.not_equal(1, 2)
        result.less(1, 2)
        result.greater(2, 1)
        result.less_equal(1, 2)
        result.greater_equal(2, 1)

    @testcase
    def test_approximate_equality(self, env, result):
        result.isclose(95, 100, 0, 5)

    @testcase
    def test_membership(self, env, result):
        result.contain(1, [1, 2, 3])
        result.not_contain("foo", "bar")

    @testcase
    def test_regex(self, env, result):
        result.regex.match("foo", "foobar")
        result.regex.not_match("foo", "bar")

    @testcase
    def test_group_assertions(self, env, result):
        result.equal("foo", "foo")

        with result.group("assertion group description") as my_group:
            my_group.equal(1, 1)
            my_group.regex.match("hello", "hello world")

            with my_group.group("sub group description") as sub_group:
                sub_group.equal("foo", "foo")

    @testcase
    def test_summary_assertions(self, env, result):
        with result.group(summarize=True, num_passing=2) as group:
            for i in range(100):
                group.equal(i, i)

    @testcase(summarize=True, num_passing=2, num_failing=3)
    def testcase_level_summarization(self, env, result):
        for i in range(100):
            result.equal(i, i)

    @testcase
    def test_exception_assertions(self, env, result):
        with result.raises(KeyError, description="key error description"):
            {}["foo"]

        with result.not_raises(TypeError):
            {}["foo"]

        with result.raises(TypeError, pattern="hello"):
            raise TypeError("hello world")

        class MyException(Exception):
            def __init__(self, num, msg):
                super(MyException, self).__init__(msg)
                self.num = num

        with result.raises(MyException, func=lambda exc: exc.num % 2 == 0):
            raise MyException(4, "exception msg")

    @testcase
    def test_equal_slices_assertions(self, env, result):
        result.equal_slices(
            expected=["a", "b", 3, 4],
            actual=[1, 2, 3, 4],
            slices=[slice(2, None)],
            description="passing equal slices",
        )

        result.equal_exclude_slices(
            expected=["a", "b", 3, 4],
            actual=[1, 2, 3, 4],
            slices=[slice(0, 2)],
            description="passing equal exclude slices",
        )

    @testcase
    def test_diff_assertions(self, env, result):
        result.diff(
            first="abc\nxyz\n",
            second="abc\nxyz\n",
            description="no difference found",
        )

        result.diff(
            first="abc \nxy z\n",
            second="abc\r\nxy\tz\r\n",
            ignore_space_change=True,
            context=True,
            description="no difference found with option -b",
        )

    @testcase
    def test_column_contain(self, env, result):
        table = [
            ["foo", "bar"],
            [1, 2],
            [10, 20],
            [30, 40],
            [0, 0],
            [100, 200],
            [1000, 2000],
            [10000, 20000],
        ]

        result.table.column_contain(
            table=table,
            column="foo",
            values=[1, 5, 10, 30, 50],
            description="column contain passing",
            limit=3,
        )

    @testcase
    def test_table_match(self, env, result):
        table = [
            ["name", "value"],
            ["aaa", 1],
            ["bbb", 2],
            ["ccc", 3],
            ["ddd", 4],
        ]

        result.table.match(
            actual=table, expected=table, description="basic table match"
        )

        result.table.match(
            actual=table, expected=table[:-1] + [[always_true, 4]]
        )

        result.table.match(
            actual=table, expected=table[:-1] + [[re.compile(r"d+"), 4]]
        )

        table_2 = [
            ["name", "value", "is_finished"],
            ["aaa", 10, True],
            ["bbb", 20, False],
            ["ccc", 30, True],
            ["ddd", 40, False],
        ]

        result.table.match(
            actual=table_2,
            expected=table,
            include_columns=["name"],
            report_all=False,
        )

        result.table.match(
            actual=table_2,
            expected=table,
            include_columns=["name"],
            report_all=True,
        )

        result.table.match(
            actual=table_2,
            expected=table,
            exclude_columns=["value", "is_finished"],
            report_all=False,
        )

        result.table.match(
            actual=table_2,
            expected=table,
            exclude_columns=["value", "is_finished"],
            report_all=True,
        )

        # All cells of column are set to `None`, which means value is missing
        for row in table[1:]:
            row[1] = None
        for row in table_2[1:]:
            row[1] = None

        result.table.match(
            actual=table_2,
            expected=table,
            include_columns=["name", "value"],
            report_all=True,
        )

        result.table.match(
            actual=table,
            expected=table_2,
            exclude_columns=["is_finished"],
            report_all=True,
        )

    @testcase
    def test_table_diff(self, env, result):
        table = [
            ["name", "value"],
            ["aaa", 1],
            ["bbb", 2],
            ["ccc", 3],
            ["ddd", 4],
        ]

        result.table.diff(
            actual=table, expected=table, description="basic table diff"
        )

        result.table.diff(
            actual=table, expected=table[:-1] + [[always_true, 4]]
        )

        result.table.diff(
            actual=table, expected=table[:-1] + [[re.compile(r"d+"), 4]]
        )

        table_2 = [
            ["name", "value", "is_finished"],
            ["aaa", 10, True],
            ["bbb", 20, False],
            ["ccc", 30, True],
            ["ddd", 40, False],
        ]

        result.table.diff(
            actual=table_2,
            expected=table,
            include_columns=["name"],
            report_all=False,
        )

        result.table.diff(
            actual=table_2,
            expected=table,
            include_columns=["name"],
            report_all=True,
        )

        result.table.diff(
            actual=table_2,
            expected=table,
            exclude_columns=["value", "is_finished"],
            report_all=False,
        )

        result.table.diff(
            actual=table_2,
            expected=table,
            exclude_columns=["value", "is_finished"],
            report_all=True,
        )

    @testcase
    def test_table_log(self, env, result):
        table = [
            ["name", "value"],
            ["aaa", 1],
            ["bbb", 2],
            ["ccc", 3],
            ["ddd", 4],
        ]

        result.table.log(table=table, description="basic table log")

        result.table.log(table=table, display_index=True)

    @testcase
    def test_xml_check(self, env, result):

        # Passing assertions
        result.xml.check(
            element="<Root><Test>Foo</Test></Root>",
            xpath="/Root/Test",
            description="basic XML check",
        )

        result.xml.check(
            element="<Root><Test>Value1</Test><Test>Value2</Test></Root>",
            xpath="/Root/Test",
            tags=["Value1", "Value2"],
        )

        result.xml.check(
            element="<Root><Test>Value1</Test><Test>Value2</Test></Root>",
            xpath="/Root/Test",
            tags=[cmp.In(["a", "b", "Value1"]), re.compile(".*lue2")],
        )

        result.xml.check(
            element="""
                <SOAP-ENV:Envelope
                   xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
                    <SOAP-ENV:Header/>
                      <SOAP-ENV:Body>
                        <ns0:message
                         xmlns:ns0="http://testplan">Hello world!</ns0:message>
                      </SOAP-ENV:Body>
                </SOAP-ENV:Envelope>
            """,
            xpath="//*/a:message",
            tags=["Hello*"],
            namespaces={"a": "http://testplan"},
        )

    @testcase
    def test_dict_check(self, env, result):

        result.dict.check(
            dictionary={"foo": 1, "bar": 2},
            has_keys=["foo"],
            absent_keys=["baz"],
            description="basic dict check",
        )

    @testcase
    def test_dict_match(self, env, result):

        result.dict.match(
            actual={"foo": 1, "bar": 2, "baz": 2},
            expected={"foo": 1, "bar": 2, "bat": 3},
            description="basic dict match",
            actual_description="description for actual",
            expected_description="description for expected",
            include_keys=["foo", "bar"],
            exclude_keys=["baz", "bat"],
        )

        result.dict.match(
            actual={"foo": 1, "bar": "hello"},
            expected={"foo": cmp.Equal(1), "bar": re.compile("he*")},
            description="match with regex & custom func",
        )

        result.dict.match(
            actual={"foo": 1, "bar": "2"},
            expected={"foo": 1, "bar": "2"},
            description="dict match checking types",
            value_cmp_func=cmp.COMPARE_FUNCTIONS["check_types"],
        )

        class AlwaysComparesTrue:
            """Object that compares equal to any other object."""

            def __eq__(self, _):
                return True

        result.dict.match(
            actual={"foo": 1, "bar": 2},
            expected={
                "foo": AlwaysComparesTrue(),
                "bar": AlwaysComparesTrue(),
            },
            description="comparison of different types",
        )

        class HelloObj:
            """Object that returns 'hello' as its str() representation."""

            def __str__(self):
                return "hello"

        result.dict.match(
            actual={"foo": 1, "bar": "hello"},
            expected={"foo": "1", "bar": HelloObj()},
            description="match with stringify method",
            value_cmp_func=cmp.COMPARE_FUNCTIONS["stringify"],
        )

    @testcase
    def test_dict_match_all(self, env, result):
        result.dict.match_all(
            values=[{"foo": 1, "bar": 2}, {"foo": 10, "bar": 20}],
            comparisons=[
                cmp.Expected({"foo": 10, "bar": 20}),
                cmp.Expected({"foo": 1, "bar": 2}),
            ],
            description="basic unordered dict match all",
        )

    @testcase
    def test_dict_log(self, env, result):
        result.dict.log({}, description="Log an empty dictionary")

        result.dict.log(
            OrderedDict(
                [
                    ("alpha", ["foobar", {"foo": "bar"}]),
                    ("beta", "hello world"),
                ]
            )
        )

    @testcase
    def test_fix_check(self, env, result):

        result.fix.check(
            msg={"foo": 1, "bar": 2},
            has_tags=["foo"],
            absent_tags=["baz"],
            description="basic fix check",
        )

    @testcase
    def test_fix_match(self, env, result):
        result.fix.match(
            actual={"foo": 1, "bar": 2, "baz": 2},
            expected={"foo": 1, "bar": 2, "bat": 3},
            description="basic fix match",
            actual_description="description for actual",
            expected_description="description for expected",
            include_tags=["foo", "bar"],
            exclude_tags=["baz", "bat"],
        )

        result.fix.match(
            actual={"foo": 1, "bar": "hello"},
            expected={"foo": cmp.Equal(1), "bar": re.compile("he*")},
            description="match with regex & custom func",
        )

        result.fix.match(
            actual={"foo": 1, "bar": 1.54},
            expected={"foo": "1", "bar": "1.54"},
            description="default untyped fixmatch will stringify",
        )

        typed_fixmsg = test_utils.FixMessage(
            (("foo", 1), ("bar", 1.54)), typed_values=True
        )
        result.fix.match(
            actual=typed_fixmsg,
            expected=typed_fixmsg.copy(),
            description="typed fixmatch will compare types",
        )

        untyped_fixmsg = test_utils.FixMessage(
            (("foo", "1"), ("bar", "1.54")), typed_values=False
        )
        result.fix.match(
            actual=typed_fixmsg,
            expected=untyped_fixmsg,
            description="mixed fixmatch will compare string values",
        )

    @testcase
    def test_fix_match_all(self, env, result):
        result.fix.match_all(
            values=[
                test_utils.FixMessage(
                    [(10914, "c1dec2c5"), (38, "500"), (44, "9")],
                    typed_values=False,
                ),
                test_utils.FixMessage(
                    [(10914, "f3ea6276"), (38, 501), (44, 9.1)],
                    typed_values=True,
                ),
            ],
            comparisons=[
                cmp.Expected(
                    test_utils.FixMessage(
                        [(10914, re.compile(".+")), (38, 501), (44, 9.10)],
                        typed_values=True,
                    )
                ),
                cmp.Expected(
                    test_utils.FixMessage(
                        [(10914, "c1dec2c5"), (38, "500"), (44, 9.0)],
                        typed_values=True,
                    )
                ),
            ],
            description="untyped / unordered fix match all",
        )

    @testcase
    def test_logfile(self, env, result):

        from testplan.common.utils.match import LogMatcher

        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()
        try:
            lm = LogMatcher(f.name)
            f = open(f.name, "r+")
            f.write("vodka\n")
            f.write("lime juice\n")
            f.flush()
            result.logfile.match(lm, r"lime juice", timeout=1)
            result.logfile.seek_eof(lm)
            with result.logfile.expect(lm, r"ginger beer", timeout=1):
                f.write("ginger beer\n")
                f.flush()
        finally:
            f.close()
            os.unlink(f.name)


def make_multitest():
    return MultiTest(name="MyMultitest", suites=[MySuite()])
