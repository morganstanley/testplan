import click


class CommandList:
    def __init__(self):
        self.commands = []

    def command(self, *args, **kwargs):
        def inner(func):
            command = click.command(*args, **kwargs)(func)
            self.commands.append(command)
            return command

        return inner

    def register_to(self, group: click.Group) -> None:
        for command in self.commands:
            group.add_command(command)
