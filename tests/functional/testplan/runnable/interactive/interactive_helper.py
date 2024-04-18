from testplan.common.utils.timing import wait


def interactive_started(plan):
    return plan.interactive.http_handler_info[0] is not None


def wait_for_interactive_start(plan):
    wait(
        lambda: interactive_started(plan),
        5,
        raise_on_timeout=True,
    )
