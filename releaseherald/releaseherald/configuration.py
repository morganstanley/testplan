import re
from pathlib import Path
from typing import Pattern, List

from pydantic import BaseModel, root_validator

from releaseherald import templates


class Configuration(BaseModel):
    config_path: Path
    version_tag_pattern: Pattern = re.compile(
        r"v(?P<version>(\d*).(\d*).(\d*))"
    )
    news_fragments_directory: Path = "news_fragments"
    insert_marker: Pattern = re.compile(
        r"^(\s)*\.\. releaseherald_insert(\s)*$"
    )
    template: Path = str(Path(templates.__path__[0]) / "news.rst")
    unreleased: bool = False
    news_file: Path = "news.rst"
    last_tag: str = ""

    class Config:
        paths_to_resolve: List[str] = ["template", "news_file"]

    def as_default_options(self):
        return {"generate": {"unreleased": self.unreleased}}

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
