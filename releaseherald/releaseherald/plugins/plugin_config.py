from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, DefaultDict

import click
from boltons.cacheutils import cached, LRI
from pydantic import BaseModel

from releaseherald.plugins.interface import CommandOptions


@dataclass
class FromCommandline:
    """
    This class can be used to annotate a PluginConfig attribute, it connect the annotated attribute to
    the passed commandline

    Attributes:
        command: the command the option need to attached to
        option: the commandline option
    """

    command: str
    option: click.Option


@dataclass
class UpdateMapping:
    field_name: str
    option_name: str


@dataclass
class CommandOptionsInfo:
    options: List[click.Option] = field(default_factory=list)
    update_mappings: List[UpdateMapping] = field(default_factory=list)


class PluginConfig(BaseModel):
    """
    A helper base class for easier declarative plugin configuration.

    - can be used with [Configuration.parse_sub_config][releaseherald.configuration.Configuration.parse_sub_config]
      for easier parsing
    - Attributes can be Annotated types, which can contain
      [FromCommandline][releaseherald.plugins.plugin_config.FromCommandline] Annotation, that make the config setting
      overridable from commandline

    #Usage

    ```python
    class MyPluginConfig(PluginConfig):
        non_overridable_value: str = "some default

        # use type Annotation to connect the attribute wit the commandline Option
        overridable_value: Annotated[str, FromCommandline(
            "generate",
            click.Option(
                param_decls=["--override"],
                help="override the overrideable value",
            )
        )] = "default for overrideable value"

    class MyPlugin:
        @releaseherald.plugins.hookimpl
        def process_config(self, config: Configuration):
            # parse the config with the helper
            self.my_config = config.parse_sub_config("my_config", MyPluginConfig)

        @releaseherald.plugins.hookimpl
        def get_command_options(self, command: str) -> Optional[CommandOptions]:
            # just use the helper to return the right thing
            return self.my_config.get_command_options(command)

        @releaseherald.plugins.hookimpl
        def on_start_command(self, command: str, kwargs: Dict[str, Any]):
            # use the helper to reflect commandline overrides in the config
            self.my_config.update(command, kwargs)
    ```
    """

    @classmethod
    @cached(LRI())
    def _get_command_options_info(cls) -> Dict[str, CommandOptionsInfo]:

        command_options: DefaultDict[str, CommandOptionsInfo] = defaultdict(
            CommandOptionsInfo
        )

        for field in cls.__fields__.values():
            metadata = getattr(field.outer_type_, "__metadata__", None)
            if not metadata:
                continue

            for annotation in metadata:
                if not isinstance(annotation, FromCommandline):
                    continue
                command = command_options[annotation.command]

                command.options.append(annotation.option)
                command.update_mappings.append(
                    UpdateMapping(field.name, annotation.option.name)
                )

        return dict(command_options)

    def get_command_options(self, command: str) -> Optional[CommandOptions]:
        """
        Generate command options from Annotated fields which can be returned directly from
        [get_command_options hook][releaseherald.plugins.hookspecs.get_command_options]

        Args:
            command: the command these command options are registered with

        Returns:
            The command options that the [get_command_options hook][releaseherald.plugins.hookspecs.get_command_options]
             expects
        """
        command_options: CommandOptionsInfo = (
            self._get_command_options_info().get(command)
        )

        if command_options:

            def default_opts_callback(default_options: Dict[str, Any]):
                for update_mapping in command_options.update_mappings:
                    default_options[update_mapping.option_name] = getattr(
                        self, update_mapping.field_name
                    )

            return CommandOptions(
                command_options.options, default_opts_callback
            )

    def update(self, command: str, kwargs: Dict[str, Any]) -> None:
        """
        Update itself from commandline options, can be used in
        [on_start_command hook][releaseherald.plugins.hookspecs.on_start_command]

        Args:
            command: the command
            kwargs: the commandline args for the command
        """
        command_options: CommandOptionsInfo = (
            self._get_command_options_info().get(command)
        )

        if command_options:
            for update_mapping in command_options.update_mappings:
                setattr(
                    self,
                    update_mapping.field_name,
                    kwargs[update_mapping.option_name],
                )
