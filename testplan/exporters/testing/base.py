""" TODO """
"""
Implements base exporter objects.
"""

try:
    from typing import TypeAlias  # >= 3.10
except ImportError:
    from typing_extensions import TypeAlias  # < 3.10

from testplan.common.exporters import BaseExporter


Exporter: TypeAlias = BaseExporter
