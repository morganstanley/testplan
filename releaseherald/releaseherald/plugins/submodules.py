from pathlib import Path
from typing import Optional, Pattern, List

from boltons.iterutils import pairwise
from git import Commit, Repo  # type: ignore

import releaseherald.plugins
from pydantic import BaseModel, root_validator, parse_obj_as

from releaseherald.configuration import (
    Configuration,
    DEFAULT_FRAGMENTS_DIR,
    DEFAULT_VERSION_TAG_PATTERN,
)
from releaseherald.plugins.base import get_tags, get_news_between_commits
from releaseherald.plugins.interface import SubmoduleNews, CommitInfo, News, MutableProxy, VersionNews


class SubmoduleConfig(BaseModel):
    name: str
    display_name: str = None  # type: ignore
    news_fragments_directory: Path = DEFAULT_FRAGMENTS_DIR
    version_tag_pattern: Pattern = DEFAULT_VERSION_TAG_PATTERN

    @root_validator
    def default_display_name(cls, values):
        values = values.copy()
        display_name = values.get("display_name")
        values["display_name"] = display_name or values["name"]
        return values


class Submodules:
    def __init__(self):
        self.config: Optional[Configuration] = None
        self.submodule_config: List[SubmoduleConfig] = []

    @releaseherald.plugins.hookimpl
    def process_config(self, config: Configuration):
        self.config = config
        submodules = getattr(config, "submodules", None)

        if submodules:
            self.submodule_config = parse_obj_as(List[SubmoduleConfig], submodules)

        setattr(config, "submodules", self.submodule_config)

    @releaseherald.plugins.hookimpl
    def get_version_news(
        self,
        repo: Repo,
        commit_from: CommitInfo,
        commit_to: CommitInfo,
        news: List[News],
        version_news: MutableProxy[VersionNews],
    ):
        submodule_news = get_submodule_news(
            commit_from.commit, commit_to.commit, self.submodule_config
        )
        version_news.value.submodule_news = submodule_news


def get_submodule_commit(commit: Commit, name: str) -> Optional[Commit]:
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

        if not submodule_from or not submodule_to:
            continue

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
