"""A discoverable task target that will be instanciated to multiple task objects"""

from testplan.runners.pools.tasks.base import task_target
from testplan.testing.multitest import MultiTest

# need to use full path specification of the module
import sub_proj1.suites

# each entry in parameters will be used to create one task object
@task_target(
    parameters=(
        # positional args to be passed to target, as a tuple or list
        ("Proj1-Suite2", None, [sub_proj1.suites.Suite2]),
        # keyword args to be passed to target, as a dict
        dict(
            name="Proj1-Suite1",
            part_tuple=(0, 2),
            suites=[sub_proj1.suites.Suite1],
        ),
        dict(
            name="Proj1-Suite1",
            part_tuple=(1, 2),
            suites=[sub_proj1.suites.Suite1],
        ),
    ),
    # additional args of Task class
    rerun=1,
    weight=1,
)
def make_multitest(name, part_tuple=None, suites=None):
    # a test target shall only return 1 runnable object
    test = MultiTest(
        name=name, suites=[cls() for cls in suites], part=part_tuple
    )
    return test


# an alternative way of specifying parts for multitest
@task_target(
    parameters=(
        dict(
            name="Proj1-Suite1-Again",
            suites=[sub_proj1.suites.Suite1],
        ),
    ),
    # instruct testplan to split each multitest task into parts
    multitest_parts=2,
    # additional args of Task class
    rerun=1,
    weight=1,
)
def make_multitest(name, suites=None):
    # a test target shall only return 1 runnable object
    test = MultiTest(name=name, suites=[cls() for cls in suites])
    return test
