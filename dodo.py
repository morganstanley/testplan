import os
from pathlib import Path
import platform
import shutil
from typing import Dict

from doit.action import CmdAction

TESTPLAN_UI_DIR = Path("testplan/web_ui/testing")
TESTPLAN_UI_SRC = TESTPLAN_UI_DIR / "src"
TESTPLAN_UI_SOURCES = list(TESTPLAN_UI_SRC.rglob("*.js")) + list(
    TESTPLAN_UI_SRC.rglob("*.jsx")
)


def UICommand(command, **kwargs):
    kwargs["cwd"] = TESTPLAN_UI_DIR
    return CmdAction(
        command,
        **kwargs,
    )


def updated_env(env_update: Dict[str, str]):
    env = os.environ.copy()
    env.update(env_update)
    return env


def task_install_ui_deps():
    target = TESTPLAN_UI_DIR / "node_modules"
    return {
        "file_dep": [
            TESTPLAN_UI_DIR / "package.json",
            TESTPLAN_UI_DIR / "pnpm-lock.yaml",
        ],
        "targets": [target],
        "actions": [UICommand("pnpm install")],
        "clean": [(shutil.rmtree, (target,))],
    }


def task_build_ui():
    target = TESTPLAN_UI_DIR / "build"
    return {
        "task_dep": ["install_ui_deps"],
        "file_dep": TESTPLAN_UI_SOURCES,
        "targets": [target],
        "actions": [
            UICommand("pnpm prebuild"),
            UICommand("pnpm build"),
        ],
        "clean": [(shutil.rmtree, (target,))],
    }


def task_black():
    def black_cmd(update):
        return f'python -m black{" --check" if not update else ""} .'

    return {
        "actions": [CmdAction(black_cmd)],
        "params": [
            {"name": "update", "short": "u", "type": bool, "default": False}
        ],
    }


def task_pylint():
    return {"actions": ["pylint --rcfile pylintrc testplan"]}


def task_lint_ui():
    return {
        "file_dep": TESTPLAN_UI_SOURCES,
        "actions": [UICommand("pnpm lint", env=updated_env({"CI": "true"}))],
        "task_dep": ["install_ui_deps"],
    }


def task_crlf_check():
    yield {"name": None}
    if platform.system() == "Linux":
        yield {
            "name": "linux",
            "actions": ["! git ls-files --eol | grep w/crlf"],
        }
    else:
        yield {"name": "notsupported", "actions": None}


def task_lint():
    return {"actions": None, "task_dep": ["black", "pylint", "crlf_check"]}


def task_test_ui():
    return {
        "file_dep": TESTPLAN_UI_SOURCES
        + list(TESTPLAN_UI_SRC.rglob("*.js.snap")),
        "actions": [
            UICommand(
                "pnpm test",
                env=updated_env({"CI": "true"}),
            )
        ],
        "task_dep": ["install_ui_deps"],
    }


def task_test():
    return {"actions": ["pytest tests --verbose"], "verbosity": 2}


def task_build():
    return {"actions": ["python -m build -w"], "task_dep": ["build_ui"]}


def task_build_dev():
    return {
        "actions": [
            CmdAction(
                "python -m build -w", env=updated_env({"DEV_BUILD": "1"})
            )
        ],
        "task_dep": ["build_ui"],
    }
