import re
from collections import OrderedDict, namedtuple

from testplan.report import Status
from testplan.testing.base import ASSERTION_INDENT
from testplan.testing.multitest import xfail, testsuite, testcase
from testplan.testing.multitest.logging import LogCaptureMixin
from testplan.testing.bdd.gherkin import DataTable as GDataTable
from testplan.testing.bdd.tag import (
    XFailTagProcessor,
    TagParams,
    apply_tag_processors,
    ExecutionGroupTagProcessor,
)


class GherkinTestSuiteBase(LogCaptureMixin):
    feature_tag_processors = [XFailTagProcessor()]
    scenario_tag_processors = [
        XFailTagProcessor(),
        ExecutionGroupTagProcessor(),
    ]

    def _pre_testcase(self, env, result, context):
        pass

    def _post_testcase(self, env, result, context):
        pass

    def _setup(self, env, result, context):
        pass

    def _teardown(self, env, result, context):
        pass

    def __init__(self, feature, step_registry, resolver):
        super(GherkinTestSuiteBase, self).__init__()
        self.feature = feature
        self.step_registry = step_registry
        self.resolver = resolver
        self.__scenario_contexts = {}
        self.__base_context = Context()

    @property
    def scenario_contexts(self):
        return self.__scenario_contexts

    def pre_testcase(self, name, env, result):
        context = Context(self.__base_context)
        self.scenario_contexts[name] = context

        with result.group(description="pre_testcase") as pre_results:
            return self._pre_testcase(env, pre_results, context)

    def post_testcase(self, name, env, result):
        context = self.scenario_contexts[name]
        with result.group(description="post_testcase") as post_results:
            self._post_testcase(env, post_results, context)

        self.scenario_contexts[name] = None

    def setup(self, env, result):
        self._setup(env, result, self.__base_context)

    def teardown(self, env, result):
        self._teardown(env, result, self.__base_context)

    def run_testcase(self, env, result, context, testcase_name):
        scenario = next(
            scenario
            for scenario in self.feature.scenarios
            if scenario.name == testcase_name
        )
        resolver = self.resolver

        for step in scenario.steps:
            text = resolver.resolve(context, step.text)
            sentence = resolver.resolve(context, step.sentence)
            argument = resolve_argument(context, resolver, step.argument)

            step_result = result.group(description=sentence)

            with step_result:
                if argument and isinstance(argument, DataTable):
                    step_result.table.log(
                        argument.data, description="Argument"
                    )
                elif argument and isinstance(argument, str):
                    step_result.log(argument, description="Argument")

                func = self.step_registry.get(text)
                if func:
                    if argument:
                        func(env, step_result, context, argument)
                    else:
                        func(env, step_result, context)

                else:
                    step_result.fail("Missing step definition")

            self.logger.log_test_status(
                sentence,
                Status.PASSED if step_result.passed else Status.FAILED,
                indent=ASSERTION_INDENT,
            )

    @classmethod
    def get_suite_class(cls, feature):
        if not testplan_safe_name(feature.name):
            raise NonTestplanSafeNameError(
                'The feature name "{}" contains non testplan safe chars "{}"'.format(
                    feature.name, NOT_TESTPLAN_NAME_SAFE_CHARS
                )
            )

        members = OrderedDict(
            [cls.create_testcase(scenario) for scenario in feature.scenarios]
        )

        suite_class = type(
            "GherkinTestSuite", (GherkinTestSuiteBase,), members
        )
        suite_class.__name__ = str(feature.name)
        tag_params = TagParams()
        tags = apply_tag_processors(
            tags=feature.tags,
            processors=cls.feature_tag_processors,
            tag_params=tag_params,
        )

        suite = testsuite(tags=tags)(suite_class)

        if tag_params.xfail:
            suite = tag_params.xfail.apply(suite)

        return suite

    @classmethod
    def create_testcase(cls, scenario):
        if not testplan_safe_name(scenario.name):
            raise NonTestplanSafeNameError(
                'The scenario name "{}" contains non testplan safe chars "{}"'.format(
                    scenario.name, NOT_TESTPLAN_NAME_SAFE_CHARS
                )
            )

        def test_function(self, env, result):
            context = self.scenario_contexts.get(scenario.name, Context())
            return self.run_testcase(
                env, result, context=context, testcase_name=scenario.name
            )

        test_function.__name__ = str(scenario.name)
        test_function.__doc__ = scenario.description

        # special scenarios are not testcases,
        #  - so we do not mark them as testcase,
        #  - we want exception to be thrown,
        #  - and we push them with special name _scenario
        if scenario.name in SPECIAL_SCENARIOS:
            return (
                "_{}".format(scenario.name),
                lambda self, env, result, context: self.run_testcase(
                    env, result, context=context, testcase_name=scenario.name
                ),
            )

        tag_params = TagParams()
        tags = apply_tag_processors(
            tags=scenario.tags,
            processors=cls.scenario_tag_processors,
            tag_params=tag_params,
        )
        testcase_args = {
            "tags": tags,
            "execution_group": tag_params.execution_group,
        }

        testcase_function = testcase(**testcase_args)(test_function)

        if tag_params.xfail:
            testcase_function = tag_params.xfail.apply(testcase_function)

        return scenario.name, testcase_function


class Context(dict):
    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError from e


def testplan_safe_name(name):
    return not NOT_TESTPLAN_NAME_SAFE_REGEX.search(name)


NOT_TESTPLAN_NAME_SAFE_CHARS = "?*[]:"
NOT_TESTPLAN_NAME_SAFE_REGEX = re.compile(r"[?*[\]:]")


class NonTestplanSafeNameError(ValueError):
    pass


def resolve_argument(context, resolver, argument):
    if isinstance(argument, str):
        return resolver.resolve(context, argument)
    if isinstance(argument, GDataTable):
        return DataTable(
            [
                [resolver.resolve(context, data) for data in row]
                for row in argument.data
            ]
        )
    return argument


PRE_TESTCASE_FUNCTION = "pre_testcase"
POST_TESTCASE_FUNCTION = "post_testcase"
SPECIAL_SCENARIOS = [
    "setup",
    "teardown",
    PRE_TESTCASE_FUNCTION,
    POST_TESTCASE_FUNCTION,
]


class DataTable:
    HEADEREXTRACTOR = re.compile("^\[(.*)]$")

    def __init__(self, data):
        self.data = data
        self._dict = None
        self.header = None
        self.Row = None  # namedtupple class type based on header

        self.__parse_header(data)

    def rows(self):
        firstrow = 1 if self.header else 0
        for r in self.data[firstrow:]:
            if self.header:
                yield self.Row(*r)
            else:
                yield r

    def dict(self):
        if not len(self.data[0]) == 2:
            raise TypeError(
                "Data Table should have exactly 2 collumns to view as a dict"
            )
        if not self._dict:  # lazy caching
            self._dict = dict(self.rows())
        return self._dict

    def __parse_header(self, data):
        self.header = []
        for field in data[0]:
            match = DataTable.HEADEREXTRACTOR.match(field)
            if match:
                self.header.append(match.group(1))
            else:
                break
        if len(self.header) < len(data[0]):
            self.header = None
        if self.header:
            self.Row = namedtuple("Row", self.header)
