from testplan.testing.multitest import testsuite, testcase

# Need to import from project root so that dependency
# is discoverable from interactive code reloader.
from my_tests.dependency import VALUE


@testsuite
class BasicSuite(object):

    @testcase(parameters=range(2))
    def basic_case(self, env, result, arg):
        result.equal(1, VALUE, description='Passing assertion')


