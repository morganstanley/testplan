import click

from testplan.cli.utils.command_list import CommandList
from testplan.exporters.testing import JSONExporter

writer_commands = CommandList()


@writer_commands.command(name="tojson")
@click.argument("output", type=click.Path())
def to_json(output):
    def to_json(result):

        exporter = JSONExporter(json_path=output)
        exporter.export(result)

        return result

    return to_json
