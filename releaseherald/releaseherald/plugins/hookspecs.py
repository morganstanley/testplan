from typing import List, Dict, Any

import pluggy
from git import Repo, Tag
from releaseherald.configuration import Configuration
from releaseherald.plugins import CommitInfo
from releaseherald.plugins.interface import (
    MutableProxy,
    VersionNews,
    News,
    Output,
    CommandOptions,
)

hookspec = pluggy.HookspecMarker("releaseherald")


@hookspec
def process_config(config: Configuration):
    pass


@hookspec
def get_command_options(command: str) -> CommandOptions:
    pass


@hookspec
def on_start_command(command: str, kwargs: Dict[str, Any]):
    pass


@hookspec
def process_tags(repo: Repo, tags: List[Tag]):
    pass


@hookspec
def process_commits(repo: Repo, tags: List[Tag], commits: List[CommitInfo]):
    pass


@hookspec
def get_news_between_commits(
    repo: Repo, commit_from: CommitInfo, commit_to: CommitInfo, news: List[News]
):
    pass


@hookspec
def get_version_news(
    repo: Repo,
    commit_from: CommitInfo,
    commit_to: CommitInfo,
    news: List[News],
    version_news: MutableProxy[VersionNews],
):
    pass


@hookspec
def process_version_news(version_news: List[VersionNews]):
    pass


@hookspec
def generate_output(version_news: List[VersionNews], output: MutableProxy[Output]):
    pass


@hookspec
def write_output(output: Output):
    pass
