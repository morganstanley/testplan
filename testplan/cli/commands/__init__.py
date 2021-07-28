from .readers import single_reader_commands, multi_reader_commands
from .writers import writer_commands
from testplan.cli.utils.command_list import CommandList


reader_commands = CommandList(commands=[*single_reader_commands.commands, *multi_reader_commands.commands])
