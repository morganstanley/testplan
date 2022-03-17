from dataclasses import dataclass
from typing import Optional, Dict, Any, List

import click
from git import Repo, Tag

import releaseherald.plugins
from releaseherald.configuration import Configuration
from releaseherald.plugins.interface import CommandOptions, CommitInfo


class LatestFilter:
    def __init__(self):
        self.__name__ = self.__class__.__name__
        self.config: Configuration = None
        self.filter_latest: bool = False

    @releaseherald.plugins.hookimpl
    def process_config(self, config: Configuration):
        self.config = config

    @releaseherald.plugins.hookimpl
    def get_command_options(self, command: str) -> Optional[CommandOptions]:

        command_options = (
            self._get_generate_options() if command == "generate" else None
        )
        return command_options

    def _get_generate_options(self) -> CommandOptions:
        options = [
            click.Option(
                param_decls=["--latest/--all"],
                is_flag=True,
                help="Flag to set if all the versions need to be presented or just the latest",
            ),
        ]

        def default_opts_callback(default_options: Dict[str, Any]):
            default_options["latest"] = self.config.latest

        return CommandOptions(options, default_opts_callback)

    @releaseherald.plugins.hookimpl
    def on_start_command(self, command: str, kwargs: Dict[str, Any]):
        if command == "generate":
            self.filter_latest = kwargs["latest"]

    @releaseherald.plugins.hookimpl(trylast=True)
    def process_commits(self, repo: Repo, tags: List[Tag], commits: List[CommitInfo]):
        if self.filter_latest and len(commits) > 2:
            trimmed_commits = commits[0:2]
            commits.clear()
            commits.extend(trimmed_commits)