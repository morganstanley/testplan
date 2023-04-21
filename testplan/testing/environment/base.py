import time
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional

from testplan.common.config import UNSET
from testplan.common.entity.base import Environment
from testplan.common.utils.timing import TimeoutException, TimeoutExceptionInfo
from testplan.testing.environment.graph import DriverDepGraph

if TYPE_CHECKING:
    from testplan.testing.base import Test

MINIMUM_CHECK_INTERVAL = 0.1


@dataclass
class DriverPocketwatch:
    """
    For time tracking for a certain driver. Its implementation must conform
    with what's in testplan.common.utils.timing.
    """

    total_wait: float
    curr_interval: float
    interval_cap: float = 0
    multiplier: float = 0
    start_time: float = 0
    last_check: float = 0

    def __post_init__(self):
        if self.interval_cap == 0:
            self.interval_cap = self.curr_interval
            self.multiplier = 1
        else:
            self.multiplier = 2

    def record_start(self):
        self.start_time = time.time()

    def should_check(self) -> bool:
        curr_time = time.time()
        if curr_time >= self.last_check + self.curr_interval:
            self.last_check = curr_time
            self.curr_interval = min(
                self.curr_interval * self.multiplier, self.interval_cap
            )
            return True
        return False


class TestEnvironment(Environment):
    def __init__(self, parent: Optional["Test"] = None):
        super().__init__(parent)

        self.__dict__["_dependency"]: Optional[DriverDepGraph] = None
        self.__dict__["_pocketwatches"]: Dict[str, DriverPocketwatch] = dict()

    def set_dependency(self, dependency: DriverDepGraph):
        for d in dependency.vertices.values():
            if (
                d.uid() not in self._resources
                or d is not self._resources[d.uid()]
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

        # here comes the new guy

        # distribute pocketwatches
        for k, v in self._dependency.vertices.items():
            if isinstance(v.started_check_interval, tuple):
                curr_interval, interval_cap = v.started_check_interval
                self._pocketwatches[k] = DriverPocketwatch(
                    v.cfg.timeout, curr_interval, interval_cap
                )
            else:
                self._pocketwatches[k] = DriverPocketwatch(
                    v.cfg.timeout, v.started_check_interval
                )

        while not self._dependency.all_drivers_started():
            iter_start = time.time()

            # schedule new drivers
            for driver in self._dependency.drivers_to_start():
                try:
                    self._pocketwatches[driver.uid()].record_start()
                    driver.start()
                except Exception:
                    self._record_resource_exception(
                        message="While starting driver [{resource_name}]\n"
                        "{traceback_exc}\n{fetch_msg}",
                        resource=driver,
                        msg_store=self.start_exceptions,
                    )
                    self._dependency.purge_drivers_to_start()
                else:
                    self._dependency.mark_starting(driver)

            # check current drivers
            # TODO: only call started_check on a selective list of drivers
            for driver in self._dependency.drivers_starting():
                watch = self._pocketwatches[driver.uid()]
                try:
                    if time.time() >= watch.start_time + watch.total_wait:
                        # we got a timed-out here
                        raise TimeoutException(
                            f"Timeout when starting {driver}. {TimeoutExceptionInfo(watch.start_time).msg()}"
                        )
                    if watch.should_check():
                        res = driver.started_check()
                    else:
                        # else of try-else will be skipped
                        continue
                except Exception:
                    self._record_resource_exception(
                        message="While waiting for driver [{resource_name}] to start\n"
                        "{traceback_exc}\n{fetch_msg}",
                        resource=driver,
                        msg_store=self.start_exceptions,
                    )
                    self._dependency.purge_drivers_to_start()
                else:
                    if res:
                        driver.logger.debug("%s started", driver)
                        self._dependency.mark_started(driver)
                        driver._after_started()

            iter_took = time.time() - iter_start
            if iter_took > 0.1:
                warnings.warn("Slow start loop...")

            # NOTE: do we want to dynamically adjust this interval?
            time.sleep(MINIMUM_CHECK_INTERVAL)
