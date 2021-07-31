"""Execution runners."""

from .pools.tasks import Task, TaskResult, RunnableTaskAdaptor
from .base import Executor
from .local import LocalRunner
