from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Union, Any, Optional, Dict

import click
import toml
from boltons.iterutils import pairwise, get_path
from git import Repo, Commit, Tag  # type: ignore
from pluggy import PluginManager

# TODO: Handle not yet committed change
from releaseherald.configuration import Configuration
from releaseherald.plugins.interface import (
    VersionNews,
    MutableProxy,
    News,
    Output,
    CommandOptions,
)
from releaseherald.plugins.manager import get_pluginmanager

CONFIG_FILE_NAME = "releaseherald.toml"
PYPROJECT_TOML = "pyproject.toml"
CONFIG_KEY_IN_PYPROJECT = ("tool", "releaseherald")


def load_config(config_path: str, config_key: Tuple = ()) -> Configuration:
    config = get_path(toml.load(config_path), config_key, default={})
    config["config_path"] = config_path
    return Configuration.parse_obj(config)


ConfigKeyPathType = Union[Tuple, Tuple[Any, ...]]


def get_config(git_repo_dir: Path) -> Tuple[Optional[Path], ConfigKeyPathType]:
    key: ConfigKeyPathType = ()
    path = git_repo_dir / CONFIG_FILE_NAME
    if not path.exists():
        path = git_repo_dir / PYPROJECT_TOML
        key = CONFIG_KEY_IN_PYPROJECT
    return path if path.exists() else None, key


@dataclass
class Context:
    repo: Repo
    config: Configuration
    pm: PluginManager


@click.group()
def cli(**kwargs):
    pass


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

    tags: List[Tag] = []
    pm.hook.process_tags(repo=repo, tags=tags)

    commits: List[Tag] = []
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

    context.pm.hook.on_start_command(command="generate", kwargs=kwargs)
    news_fragments = collect_news_fragments(
        repo,
        pm=context.pm,
    )

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
def setup(ctx: click.Context, git_dir, config) -> Tuple[Dict[str, Any], Context]:
    repo = Repo(path=git_dir, search_parent_directories=True)

    config_key: ConfigKeyPathType = ()
    git_working_dir = Path(str(repo.working_dir))
    if not config:
        config, config_key = get_config(git_working_dir)

    configuration = (
        load_config(config, config_key)
        if config
        else Configuration(config_path=git_working_dir)
    )

    pm = get_pluginmanager(configuration)

    generate_command_options: List[CommandOptions] = pm.hook.get_command_options(
        command="generate"
    )

    for option in generate_command_options:
        generate.params.extend(option.options)
        Configuration.Config.default_options_callbacks["generate"].append(
            option.default_opts_callback
        )

    defaults = configuration.as_default_options()
    context = Context(repo=repo, config=configuration, pm=pm)
    return defaults, context


cli.params = setup.params
default_map, context_obj = setup.main(standalone_mode=False)

def main():
    cli.main(default_map=default_map, obj=context_obj)

if __name__ == "__main__":
    main()
