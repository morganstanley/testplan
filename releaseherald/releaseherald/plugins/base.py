import uuid
from dataclasses import field, dataclass
from io import StringIO
from itertools import takewhile
from pathlib import Path
from typing import List, Pattern, Dict, Any, Optional

import click
from git import Repo, Tag, Commit  # type: ignore
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

import releaseherald.plugins
from releaseherald.configuration import Configuration
from releaseherald.plugins import CommitInfo
from releaseherald.plugins.interface import (
    VersionNews,
    MutableProxy,
    News,
    Output,
    CommandOptions,
)


class BasePlugin:
    def __init__(self):
        self.__name__ = self.__class__.__name__
        self.config: Configuration = None

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
                param_decls=["--unreleased/--released"],
                is_flag=True,
                help="Flag to set if the changes from the last version label should be included or not",
            ),
        ]

        def default_opts_callback(default_options: Dict[str, Any]):
            default_options["unreleased"] = self.config.unreleased

        return CommandOptions(options, default_opts_callback)

    @releaseherald.plugins.hookimpl(tryfirst=True)
    def process_tags(self, repo: Repo, tags: List[Tag]):
        tags.clear()

        all_tags = get_tags(repo, self.config.version_tag_pattern)

        # tear of things after last tag
        last_tag_name = self.config.last_tag or ROOT_TAG
        last_tag = repo.tags[last_tag_name] if last_tag_name in repo.tags else None
        if last_tag:
            tags.extend(takewhile(lambda tag: tag != last_tag, all_tags))
            tags.append(last_tag)
        else:
            tags.extend(all_tags)

    @releaseherald.plugins.hookimpl(tryfirst=True)
    def process_commits(self, repo: Repo, tags: List[Tag], commits: List[CommitInfo]):
        commits.clear()
        commits.extend(CommitInfo(tag=tag, commit=tag.commit) for tag in tags)
        if self.config.unreleased and (
            not commits or (commits and repo.head.commit != commits[0].commit)
        ):
            commits.insert(0, CommitInfo(tag=None, commit=repo.head.commit))

    @releaseherald.plugins.hookimpl(tryfirst=True)
    def get_news_between_commits(
        self,
        repo: Repo,
        commit_from: CommitInfo,
        commit_to: CommitInfo,
        news: List[News],
    ):
        news.clear()
        git_news = get_news_between_commits(
            commit_from.commit,
            commit_to.commit,
            self.config.news_fragments_directory,
        )
        news.extend(git_news)

    @releaseherald.plugins.hookimpl(tryfirst=True)
    def get_version_news(
        self,
        repo: Repo,
        commit_from: CommitInfo,
        commit_to: CommitInfo,
        news: List[News],
        version_news: MutableProxy[VersionNews],
    ):
        version_news.value = VersionNews(
            news=news,
            tag=commit_to.name,
            version=get_version(commit_to.name, self.config.version_tag_pattern),
            from_commit=commit_from,
            to_commit=commit_to,
            date=commit_to.date,
        )


class GenerateParams(BaseModel):
    update: bool
    target: Optional[str]


class BaseOutputPlugin:
    def __init__(self):
        self.__name__ = self.__class__.__name__
        self.config: Configuration = None
        self.generate_command_params: GenerateParams = None

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
                param_decls=["--update/--no-update"],
                is_flag=True,
                help="Flag to set if the news should be rendered into the news file (--update), or just presented in it's own",
            ),
            click.Option(
                param_decls=["--target", "-t"],
                help="Path of target file, if present the generated result is written to target, else to stdout",
            ),
        ]

        def default_opts_callback(default_options: Dict[str, Any]):
            default_options.update(
                {
                    "update": self.config.update,
                    "target": self.config.target,
                }
            )

        return CommandOptions(options, default_opts_callback)

    @releaseherald.plugins.hookimpl
    def on_start_command(self, command: str, kwargs: Dict[str, Any]):
        if command == "generate":
            self.generate_command_params = GenerateParams(**kwargs)

    @releaseherald.plugins.hookimpl
    def generate_output(
        self, version_news: List[VersionNews], output: MutableProxy[Output]
    ):
        template_path = Path(self.config.template)

        jinja_env = Environment(
            loader=FileSystemLoader(template_path.parent),
            trim_blocks=True,
        )

        template = jinja_env.get_template(template_path.name)
        news_str = template.render(news=version_news)

        output.value = Output(format=template_path.suffix[1:], content=news_str)

    @releaseherald.plugins.hookimpl
    def write_output(self, output: Output):
        if self.generate_command_params.update:
            result = update_news_file(
                output.content,
                self.config.news_file,
                self.config.insert_marker,
            )
        else:
            result = output.content

        if not self.generate_command_params.target:
            print(result)
            return

        with open(self.generate_command_params.target, "wt") as file:
            file.write(result)


def get_tags(repo: Repo, version_tag_pattern: Pattern):
    tags = [
        tag
        for tag in repo.tags
        if version_tag_pattern.match(tag.name)
        and repo.is_ancestor(tag.commit, repo.head.commit)
    ]
    tags.sort(key=lambda tag: tag.commit.committed_date, reverse=True)
    return tags


ROOT_TAG = "RELEASEHERALD_ROOT"


def get_news_between_commits(
    commit1: Commit, commit2: Commit, news_fragment_dir: Path
) -> List[News]:
    diffs = commit1.diff(commit2)
    paths = [
        diff.a_path
        for diff in diffs
        if diff.change_type in ("A", "C", "R", "M")
        and news_fragment_dir == Path(diff.a_path).parent
    ]
    return [
        News(file_name=path, content=file_content_from_commit(commit2, path))
        for path in paths
    ]


def file_content_from_commit(commit2: Commit, path: str):
    news_file = commit2.tree / path
    return news_file.data_stream.read().decode("utf-8")


def get_version(tag_name: str, version_tag_pattern: Pattern):
    match = version_tag_pattern.match(tag_name)
    version = tag_name
    if match:
        version = match.groupdict().get("version", tag_name)

    return version


def update_news_file(news_str: str, news_file: Path, insert_marker: Pattern):
    changed_file = False
    output = StringIO()
    with open(news_file) as f:
        for line in f:
            output.write(line)
            if insert_marker.match(line):
                changed_file = True
                output.write(news_str)

    if not changed_file:
        raise UserWarning("No insert line in Newsfile")

    return output.getvalue()
