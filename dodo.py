import os
from pathlib import Path
import platform
import shutil
from typing import Dict
import webbrowser

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
        "doc": "Install UI dependencies (use pnpm/node)",
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
        "doc": "Build the UI bundle",
    }


def task_ruff_fmt():
    def ruff_fmt_cmd(update):
        return f"ruff format{' --check' if not update else ''}"

    return {
        "actions": [CmdAction(ruff_fmt_cmd)],
        "params": [
            {"name": "update", "short": "u", "type": bool, "default": False}
        ],
        "doc": "Run blcak formatter check. Usi it before commit :)",
    }


def task_pylint():
    return {
        "actions": ["pylint --rcfile pylintrc testplan"],
        "doc": "Run pylint",
    }


def task_lint_ui():
    return {
        "file_dep": TESTPLAN_UI_SOURCES,
        "actions": [UICommand("pnpm lint", env=updated_env({"CI": "true"}))],
        "task_dep": ["install_ui_deps"],
        "doc": "Run lint on UI javascript code",
    }


def task_crlf_check():
    yield {
        "name": None,
        "doc": "Check that no crlf in source files",
    }
    if platform.system() == "Linux":
        yield {
            "name": "linux",
            "actions": ["! git ls-files --eol | grep w/crlf"],
        }
    else:
        yield {"name": "notsupported", "actions": None}


def task_lint():
    return {
        "actions": None,
        "task_dep": ["ruff_fmt", "pylint", "crlf_check"],
        "doc": "Run lint on python and javascript code",
    }


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
        "doc": "Test the UI code",
    }


def task_test():
    return {
        "actions": ["pytest tests --verbose"],
        "verbosity": 2,
        "doc": "Test the python code",
    }


def task_build():
    return {
        "actions": ["uv build --wheel"],
        "task_dep": ["build_ui"],
        "doc": "Build a wheel package",
    }


def task_build_dev():
    return {
        "actions": [
            CmdAction("uv build --wheel", env=updated_env({"DEV_BUILD": "1"}))
        ],
        "task_dep": ["build_ui"],
        "doc": "Build a dev package (just a version number difference)",
    }


def task_build_docs():
    def open_browser(open_browser):
        if open_browser:
            webbrowser.open(str(Path("doc/en/html/index.html").absolute()))

    return {
        "actions": [
            CmdAction("python -m sphinx -b html . html", cwd=Path("doc/en")),
            open_browser,
        ],
        "params": [
            {
                "name": "open_browser",
                "short": "o",
                "type": bool,
                "default": False,
            }
        ],
        "doc": "Build the documentation",
    }
