from collections import defaultdict
from dataclasses import dataclass
from itertools import product
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
)

from pulp import (
    PULP_CBC_CMD,
    LpConstraint,
    LpMinimize,
    LpProblem,
    LpStatus,
    LpVariable,
    lpSum,
)

from testplan.common.config import UNSET
from testplan.common.entity.base import Environment

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from testplan.testing.base import Test
    from testplan.testing.multitest.driver import Driver


# XXX: do we need to uniform types of exceptions?
# XXX: apply vertices & edges length limit?

TIME_UNIT = 1  # schedule time unit in seconds
LONG_PERIOD_OF_TIME = 100000  # testplan should timeout after these seconds


@dataclass
class DriverDepGraph:
    """classical edge list"""

    vertices: Set["Driver"]
    edges: Set[Tuple["Driver", "Driver"]]

    @classmethod
    def new(cls) -> "DriverDepGraph":
        return cls(set(), set())


def _parse_err(msg: str) -> TypeError:
    return TypeError(
        f"Wrong type used in Testplan Driver dependency definition. {msg}"
    )


def parse_dependency(input: Any) -> DriverDepGraph:
    """
    The following dependency definition

    {
        A: (B, C),
        (B, C): [D, E]:
        E: F
    }

    will be parsed into

    [A -> B, A -> C, B -> D, B -> E, C -> D, C -> E, E -> F]
    """

    from testplan.testing.multitest.driver import Driver

    if not isinstance(input, dict):
        raise _parse_err("Python dict expected.")

    g = DriverDepGraph.new()

    for k, v in input.items():
        if not (
            isinstance(k, Driver)
            or (
                isinstance(k, Iterable)
                and all(isinstance(x, Driver) for x in k)
            )
        ):
            raise _parse_err(
                "Driver or flat collection of Driver expected for dict keys."
            )

        if not (
            isinstance(v, Driver)
            or (
                isinstance(v, Iterable)
                and all(isinstance(x, Driver) for x in v)
            )
        ):
            raise _parse_err(
                "Driver or flat collection of Driver expected for dict values."
            )

        if isinstance(k, Driver):
            k = (k,)
        if isinstance(v, Driver):
            v = (v,)

        for s, e in product(k, v):
            g.vertices.add(s)
            g.vertices.add(e)
            g.edges.add((s, e))

    return g


DUMMY_VARIABLE = LpVariable("?", 1, -1)


@dataclass
class DriverVariable:
    driver_uid: str
    start: LpVariable = DUMMY_VARIABLE
    elapsed: LpVariable = DUMMY_VARIABLE

    def __post_init__(self):
        self.start = LpVariable(f"a_{self.driver_uid}", 0, None)
        self.elapsed = LpVariable(
            f"b_{self.driver_uid}", LONG_PERIOD_OF_TIME, None
        )


DriverVariableMap: TypeAlias = Dict[str, DriverVariable]


class TestEnvironment(Environment):
    def __init__(self, parent: Optional["Test"] = None):
        super().__init__(parent)

        self.__dict__["_dependency"]: Optional[DriverDepGraph] = None
        self.__dict__["_problem"]: Optional[LpProblem] = None
        self.__dict__["_variables"]: Optional[DriverVariableMap] = None

    def set_dependency(self, dependency: DriverDepGraph):
        """
        Validate & generate initial driver schedule based on input dependency.
        """
        for d in dependency.vertices:
            if d.uid() not in self._resources or id(d) != id(
                self._resources[d.uid()]
            ):
                raise ValueError(
                    f"Driver {d} used in `dependency` parameter "
                    "while not being declared in `environment` parameter."
                )
        for d in self._resources.values():
            if d.async_start is not UNSET:
                raise ValueError(
                    f"`async_start` parameter of driver {d} should not "
                    "be set if driver dependency is specified."
                )

        self._dependency = dependency

        # leverage PuLP as scheduler as well as cycle detector
        self._problem = LpProblem("aha", LpMinimize)
        self._variables: DriverVariableMap = {}

        for d_uid in self._resources.keys():
            self._variables[d_uid] = DriverVariable(d_uid)

        self._problem += lpSum([v.start for v in self._variables.values()])
        for side_a, side_b in self._dependency.edges:
            self._problem += self._gen_dep_constraint(side_a, side_b)

        # use built-in lp solver
        ret = self._problem.solve(PULP_CBC_CMD(msg=False, timeLimit=10))
        # -1 for no solution exists, 0 for no solution found, 1 for solution found
        if ret == -1:
            raise ValueError(
                "Unable to work out any schedule, possibly due to cyclic dependency."
            )
        if ret != 1:
            raise RuntimeError(
                "Internal driver scheduler error, "
                f"solver reporting status {LpStatus[self._problem.status]}."
            )

    def _gen_dep_constraint(
        self, side_a: "Driver", side_b: "Driver"
    ) -> LpConstraint:
        """We first play the Side-A of a cassette."""
        return (
            self._variables[side_a.uid()].start
            + self._variables[side_a.uid()].elapsed
            <= self._variables[side_b.uid()].start
        )

    def start_in_pool(self, *_):
        raise RuntimeError(
            "TestEnvironment.start_in_pool: Would not be invoked by design."
        )

    def stop_in_pool(self, *_):
        raise RuntimeError(
            "TestEnvironment.stop_in_pool: Would not be invoked by design."
        )

    def start(self):
        """
        Start the drivers either in the legacy way or following the driver dependency.
        """
        if self._dependency is None:
            # we got no dependency declared, go with the legacy way,
            # override `async_start` of drivers
            for d in self._resources.values():
                if d.async_start is UNSET:
                    d.async_start = False
            return super().start()

        buckets = defaultdict(list)
        for v in self._variables.values():
            buckets[int(v.start.value())].append(v.driver_uid)

        for k in sorted(buckets.keys()):
            # we tend to have a consistant behaviour here
            self._naive_batch_start_drivers(
                self._resources[d_uid] for d_uid in sorted(buckets[k])
            )

    # currently we don't have non-blocking start-check callbacks on
    # individual drivers, we can't implement a "smarter" driver scheduler

    # driver start time is lower-bounded by the sum of the starting time of
    # the slowest driver in each batch

    def _naive_batch_start_drivers(self, drivers: List["Driver"]):
        wait_started: List["Driver"] = []
        for driver in drivers:
            try:
                driver.start()
            except Exception:
                self._record_resource_exception(
                    message="While starting driver [{resource_name}]\n"
                    "{traceback_exc}\n{fetch_msg}",
                    resource=driver,
                    msg_store=self.start_exceptions,
                )
            else:
                wait_started.append(driver)

        for driver in wait_started:
            try:
                driver.wait(driver.STATUS.STARTED)
            except Exception:
                self._record_resource_exception(
                    message="While waiting for driver [{resource_name}] to start\n"
                    "{traceback_exc}\n{fetch_msg}",
                    resource=driver,
                    msg_store=self.start_exceptions,
                )
            else:
                driver.logger.debug("%s started", driver)
