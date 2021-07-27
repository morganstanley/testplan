from email.policy import default

import click

from testplan.cli.utils.command_list import CommandList
from testplan.common.utils.thread import interruptible_join
from testplan.exporters.testing import JSONExporter, WebServerExporter

writer_commands = CommandList()


@writer_commands.command(name="tojson")
@click.argument("output", type=click.Path())
def to_json(output):
    def to_json(result):

        exporter = JSONExporter(json_path=output)
        exporter.export(result)

        return result

    return to_json


@writer_commands.command(name="display")
@click.option("--port", "-p", type=int, default=0)
def display(port):
    def display(result):
        try:
            exporter = WebServerExporter(ui_port=port)
            exporter.export(result)
            interruptible_join(exporter._web_server_thread)

        except KeyboardInterrupt:
            exporter._web_server_thread.stop()

        return result

    return display
