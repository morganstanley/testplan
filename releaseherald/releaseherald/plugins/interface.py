import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Generic, TypeVar

import click
from git import TagReference, Commit  # type: ignore

from releaseherald.configuration import DefaultOptionsCallable

VT = TypeVar("VT")


@dataclass
class GenerateCommandOptions:
    options: List[click.Option]
    default_opts_callback: DefaultOptionsCallable


class MutableProxy(Generic[VT]):
    def __init__(self, value: Optional[VT] = None):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value: Optional[VT]):
        self._value = value


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


@dataclass
class News:
    file_name: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubmoduleNews:
    name: str
    display_name: str
    news: List[News] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VersionNews:
    news: List[News]
    tag: str
    version: str
    from_commit: CommitInfo
    to_commit: CommitInfo
    date: datetime.datetime
    submodule_news: List[SubmoduleNews] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Output:
    format: str
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
