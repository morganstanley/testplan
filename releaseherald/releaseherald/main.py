from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import click
import toml
from boltons.iterutils import pairwise, get_path
from git import Repo, Commit
from pluggy import PluginManager

# TODO: Handle not yet committed change
from releaseherald.configuration import Configuration, SubmoduleConfig
from releaseherald.plugins.base import get_tags, get_news_between_commits
from releaseherald.plugins.interface import (
    SubmoduleNews,
    VersionNews,
    MutableProxy,
    News,
    Output,
    GenerateCommandOptions,
)
from releaseherald.plugins.manager import get_pluginmanager

CONFIG_FILE_NAME = "releaseherald.toml"
PYPROJECT_TOML = "pyproject.toml"
CONFIG_KEY_IN_PYPROJECT = ("tool", "releaseherald")


def load_config(config_path: str, config_key: Tuple = ()) -> Configuration:
    config = get_path(toml.load(config_path), config_key, default={})
    config["config_path"] = config_path
    return Configuration.parse_obj(config)


def get_config(git_repo_dir: str) -> Tuple[str, Tuple]:
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
    pm: PluginManager = None


@click.group()
def cli(**kwargs):
    pass


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


# TODO: move submodule handling to plugin

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

        snews = SubmoduleNews(name=submodule.name, display_name=submodule.display_name)

        for c_to, c_from in pairwise(commits):
            snews.news.extend(
                get_news_between_commits(
                    c_from, c_to, submodule.news_fragments_directory
                )
            )
        news.append(snews)
    return news


def get_version_news(pm, repo, commit_from, commit_to):
    news: List[News] = []
    pm.hook.get_news_between_commits(
        repo=repo, commit_from=commit_from, commit_to=commit_to, news=news
    )

    proxy = MutableProxy[VersionNews]()
    pm.hook.get_version_news(
        repo=repo,
        commit_from=commit_from,
        commit_to=commit_to,
        news=news,
        version_news=proxy,
    )
    return proxy.value


def collect_news_fragments(
    repo: Repo,
    pm: PluginManager,
) -> List[VersionNews]:

    tags = []
    pm.hook.process_tags(repo=repo, tags=tags)

    commits = []
    pm.hook.process_commits(repo=repo, tags=tags, commits=commits)

    version_news = [
        get_version_news(pm, repo, commit_from, commit_to)
        for commit_to, commit_from in pairwise(commits)
    ]

    pm.hook.process_version_news(version_news=version_news)

    return version_news


def generate_news(news_fragments, template):
    return template.render(news=news_fragments)


@cli.command()
@click.pass_context
def generate(ctx: click.Context, **kwargs):
    context: Context = ctx.obj

    config = context.config
    repo = context.repo

    context.pm.hook.process_generate_command_params(kwargs=kwargs)

    news_file = config.news_file

    news_fragments = collect_news_fragments(
        repo,
        pm=context.pm,
    )

    # TODO: do latest logic in plugin
    # if latest:
    #     news_fragments = news_fragments[0:1]

    output = MutableProxy[Output]()
    context.pm.hook.generate_output(version_news=news_fragments, output=output)

    context.pm.hook.write_output(output=output.value)


@click.command(
    add_help_option=False,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option("--git-dir", default="./", help="Path to the git repo to use.")
@click.option(
    "--config",
    type=click.File(),
    help="Path to the config file, if not provided releaseherald.toml or pyproject.toml usde from git repo root.",
)
@click.pass_context
def setup(ctx: click.Context, git_dir, config):
    repo = Repo(path=git_dir, search_parent_directories=True)

    config_key = ()
    if not config:
        config, config_key = get_config(repo.working_dir)

    configuration = (
        load_config(config, config_key)
        if config
        else Configuration(config_path=repo.working_dir)
    )

    pm = get_pluginmanager(configuration)

    generate_command_options: List[
        GenerateCommandOptions
    ] = pm.hook.get_generate_command_options()

    for option in generate_command_options:
        generate.params.extend(option.options)
        Configuration.Config.default_options_callbacks["generate"].append(
            option.default_opts_callback
        )

    ctx.default_map = configuration.as_default_options()

    ctx.ensure_object(Context)
    ctx.obj.repo = repo
    ctx.obj.config = configuration
    ctx.obj.pm = pm

    return ctx.obj


cli.params = setup.params

if __name__ == "__main__":
    retval = setup.main(standalone_mode=False)

    cli.main(obj=retval)
