"""
Implements command list type.
"""
from typing import List, Callable

import click


class CommandList:
    """
    Utility class, used for creating, storing, and registering Click commands.
    """

    def __init__(self, commands: List[click.Command] = None) -> None:
        """
        :param commands: list of Click commands
        """
        self.commands = commands or []

    def command(self, *args, **kwargs) -> Callable:
        """
        Decorator that creates new Click command and adds it to command list.
        """

        def inner(func):
            command = click.command(*args, **kwargs)(func)
            self.commands.append(command)
            return command

        return inner

    def register_to(self, group: click.Group) -> None:
        """
        Registers all commands to the given group.

        :param group: Click group to register the commands to
        """
        for command in self.commands:
            group.add_command(command)
