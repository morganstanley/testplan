import re
from pathlib import Path
from typing import Pattern, List

from pydantic import BaseModel, root_validator

from releaseherald import templates

DEFAULT_FRAGMENTS_DIR = "news_fragments"

DEFAULT_VERSION_TAG_PATTERN = re.compile(r"(?P<version>(\d*)\.(\d*)\.(\d*))")


class SubmoduleConfig(BaseModel):
    name: str
    display_name: str = None
    news_fragments_directory: Path = DEFAULT_FRAGMENTS_DIR
    version_tag_pattern: Pattern = DEFAULT_VERSION_TAG_PATTERN

    @root_validator
    def default_display_name(cls, values):
        values = values.copy()
        display_name = values.get("display_name")
        values["display_name"] = display_name or values["name"]
        return values


class Configuration(BaseModel):
    config_path: Path
    version_tag_pattern: Pattern = DEFAULT_VERSION_TAG_PATTERN
    news_fragments_directory: Path = DEFAULT_FRAGMENTS_DIR
    insert_marker: Pattern = re.compile(
        r"^(\s)*\.\. releaseherald_insert(\s)*$"
    )
    template: Path = str(Path(templates.__path__[0]) / "news.rst")
    unreleased: bool = False
    news_file: Path = "news.rst"
    target: Path = None
    last_tag: str = ""
    latest: bool = False
    update: bool = True
    submodules: List[SubmoduleConfig] = []

    class Config:
        paths_to_resolve: List[str] = ["template", "news_file"]

    def as_default_options(self):
        return {
            "generate": {
                "unreleased": self.unreleased,
                "update": self.update,
                "latest": self.latest,
                "target": self.target,
            }
        }

    @root_validator
    def resolve_paths(cls, values):
        root = Path(values["config_path"]).parent
        values = values.copy()
        for path_config in cls.__config__.paths_to_resolve:
            path = Path(values[path_config])
            values[path_config] = str(
                path if path.is_absolute() else root / path
            )

        return values