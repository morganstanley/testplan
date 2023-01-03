import click

from testplan.cli.commands import single_reader_commands
from testplan.cli.commands.writers import (
    display as display_command,
)


# here we create a display command that does the same with
# a single parsed result as the convert from* ... display would do


@click.group(name="display")
def display(*args, **kwargs):
    pass


display.help = display_command.help
display.params = display_command.params


@display.result_callback()
def run_actions(parse_action, **kwargs):

    result = parse_action()
    # now we have the result just call the display writer
    click.get_current_context().invoke(display_command, **kwargs)(result)


single_reader_commands.register_to(display)
