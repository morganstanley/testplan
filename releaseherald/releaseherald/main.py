import datetime
from dataclasses import dataclass, field
from io import StringIO
from itertools import takewhile
from pathlib import Path
from typing import List, Tuple, Pattern, Optional

import click
import toml
from boltons.iterutils import pairwise, get_path
from git import Repo, Commit, TagReference
from jinja2 import Environment, FileSystemLoader
from releaseherald.configuration import Configuration, SubmoduleConfig

# TODO: Handle not yet committed change

ROOT_TAG = "RELEASEHERALD_ROOT"

CONFIG_FILE_NAME = "releaseherald.toml"
PYPROJECT_TOML = "pyproject.toml"
CONFIG_KEY_IN_PYPROJECT = ("tool", "releaseherald")


def load_config(config_path: str, config_key: Tuple = ()) -> Configuration:
    config = get_path(toml.load(config_path), config_key, default={})
    config["config_path"] = config_path
    return Configuration.parse_obj(config)


def get_config(git_repo_dir: str) -> (str, Tuple):
    key = ()
    path = Path(git_repo_dir) / CONFIG_FILE_NAME
    if not path.exists():
        path = Path(git_repo_dir) / PYPROJECT_TOML
        key = CONFIG_KEY_IN_PYPROJECT
    return str(path) if path.exists() else None, key


@dataclass
class Context:
    repo: Repo = None
    config: Configuration = None


@click.group()
@click.option("--git-dir", default="./")
@click.option("--config", type=click.File())
@click.pass_context
def cli(ctx: click.Context, git_dir, config):
    repo = Repo(path=git_dir, search_parent_directories=True)

    config_key = ()
    if not config:
        config, config_key = get_config(repo.working_dir)

    configuration = (
        load_config(config, config_key) if config else Configuration()
    )

    ctx.default_map = configuration.as_default_options()

    ctx.ensure_object(Context)
    ctx.obj.repo = repo
    ctx.obj.config = configuration


def get_tags(repo: Repo, version_tag_pattern: Pattern):
    tags = [
        tag
        for tag in repo.tags
        if version_tag_pattern.match(tag.name)
        and repo.is_ancestor(tag.commit, repo.head)
    ]
    tags.sort(key=lambda tag: tag.commit.committed_date, reverse=True)
    return tags


@dataclass
class News:
    file_name: str
    content: str


@dataclass
class SubmoduleNews:
    name: str
    display_name: str
    news: List[News] = field(default_factory=list)


@dataclass
class VersionNews:
    news: List[News]
    tag: str
    version: str
    date: datetime.datetime
    submodule_news: List[SubmoduleNews]


def get_news_between_commits(
    commit1: Commit, commit2: Commit, news_fragment_dir: str
) -> List[News]:
    diffs = commit1.diff(commit2)
    paths = [
        diff.a_path
        for diff in diffs
        if diff.change_type in ("A", "C", "R", "M")
        and Path(news_fragment_dir) == Path(diff.a_path).parent
    ]
    return [
        News(file_name=path, content=file_content_from_commit(commit2, path))
        for path in paths
    ]


def file_content_from_commit(commit2: Commit, path: str):
    news_file = commit2.tree / path
    return news_file.data_stream.read().decode("utf-8")


@dataclass
class CommitInfo:
    tag: Optional[TagReference]
    commit: Commit

    @property
    def name(self) -> str:
        return self.tag.name if self.tag else "Unreleased"

    @property
    def date(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            self.tag.tag.tagged_date
            if self.tag and self.tag.tag
            else self.commit.committed_date
        )


def get_commits(
    repo: Repo, tags, include_head, include_root
) -> List[CommitInfo]:
    commits = [CommitInfo(tag=tag, commit=tag.commit) for tag in tags]
    if include_head and (
        not commits or (commits and repo.head.commit != commits[0].commit)
    ):
        commits.insert(0, CommitInfo(tag=None, commit=repo.head.commit))
    if include_root and ROOT_TAG in repo.tags:
        root_tag = repo.tags[ROOT_TAG]
        commits.append(CommitInfo(tag=root_tag, commit=root_tag.commit))

    return commits


def get_version(tag_name: str, version_tag_pattern: Pattern):
    match = version_tag_pattern.match(tag_name)
    version = tag_name
    if match:
        version = match.groupdict().get("version", tag_name)

    return version


def get_submodule_commit(commit: Commit, name: str) -> Commit:
    repo = commit.repo
    try:
        submodule = repo.submodules[name]
        sha = (commit.tree / submodule.path).hexsha
    except KeyError as e:
        # this case the submodule either not exist or not exist at that commit we are looking into
        return None

    srepo = submodule.module()
    return srepo.commit(sha)


def get_submodule_news(
    commit_from: Commit, commit_to: Commit, submodules: List[SubmoduleConfig]
) -> List[SubmoduleNews]:
    news = []
    for submodule in submodules:
        submodule_from = get_submodule_commit(commit_from, submodule.name)
        submodule_to = get_submodule_commit(commit_to, submodule.name)
        srepo = submodule_from.repo
        tag_commits = [
            tag.commit
            for tag in get_tags(srepo, submodule.version_tag_pattern)
            if srepo.is_ancestor(submodule_from, tag.commit)
            and srepo.is_ancestor(tag.commit, submodule_to)
        ]

        commits = [submodule_to, *tag_commits, submodule_from]

        snews = SubmoduleNews(
            name=submodule.name, display_name=submodule.display_name
        )

        for c_to, c_from in pairwise(commits):
            snews.news.extend(
                get_news_between_commits(
                    c_from, c_to, submodule.news_fragments_directory
                )
            )
        news.append(snews)
    return news


def collect_news_fragments(
    repo: Repo,
    include_unreleased: bool,
    version_tag_pattern: Pattern,
    news_fragment_dir: str,
    last_tag: str,
    submodules: List[SubmoduleConfig],
) -> List[VersionNews]:
    tags = get_tags(repo, version_tag_pattern)

    # tear of things after last tag
    last_tag = repo.tags[last_tag] if last_tag in repo.tags else None
    if last_tag:
        tags = list(takewhile(lambda tag: tag != last_tag, tags))
        tags.append(last_tag)

    commits = get_commits(
        repo, tags, include_unreleased, include_root=not last_tag
    )

    result = [
        VersionNews(
            news=get_news_between_commits(
                commit_from.commit, commit_to.commit, news_fragment_dir
            ),
            tag=commit_to.name,
            version=get_version(commit_to.name, version_tag_pattern),
            date=commit_to.date,
            submodule_news=get_submodule_news(
                commit_from.commit, commit_to.commit, submodules
            ),
        )
        for commit_to, commit_from in pairwise(commits)
    ]

    return result


def generate_news(news_fragments, template):
    return template.render(news=news_fragments)


def update_news_file(news_str: str, news_file: str, insert_marker: Pattern):
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


@cli.command()
@click.option("--unreleased/--released", is_flag=True)
@click.option("--update/--no-update", is_flag=True)
@click.option("--latest/--all", is_flag=True)
@click.option(
    "--target",
    "-t",
)
@click.pass_context
def generate(
    ctx: click.Context,
    update: bool,
    unreleased: bool,
    latest: bool,
    target: str,
):
    context: Context = ctx.obj

    config = context.config
    news_file = config.news_file

    repo = context.repo

    news_fragments = collect_news_fragments(
        repo,
        include_unreleased=unreleased,
        version_tag_pattern=config.version_tag_pattern,
        news_fragment_dir=config.news_fragments_directory,
        last_tag=config.last_tag,
        submodules=config.submodules,
    )

    template_path = Path(config.template)
    jinja_env = Environment(
        loader=FileSystemLoader(template_path.parent),
        trim_blocks=True,
    )

    template = jinja_env.get_template(template_path.name)

    if latest:
        news_fragments = news_fragments[0:1]

    news_str = generate_news(news_fragments, template)

    if update:
        result = update_news_file(news_str, news_file, config.insert_marker)
    else:
        result = news_str

    if not target:
        print(result)
        return

    with open(target, "wt") as file:
        file.write(result)


if __name__ == "__main__":
    cli()
