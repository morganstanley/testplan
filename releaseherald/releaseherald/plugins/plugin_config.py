from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, DefaultDict

import click
from boltons.cacheutils import cached, LRI
from pydantic import BaseModel

from releaseherald.plugins.interface import CommandOptions


@dataclass
class FromCommandline:
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

    def update(self, command: str, kwargs: Dict[str, Any]):
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
