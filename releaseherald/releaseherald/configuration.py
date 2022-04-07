import re
from collections import defaultdict
from pathlib import Path
from typing import Pattern, List, Callable, Dict, Any, Optional

from pydantic import BaseModel, root_validator

from releaseherald import templates

DEFAULT_FRAGMENTS_DIR = Path("news_fragments")

DEFAULT_VERSION_TAG_PATTERN = re.compile(r"(?P<version>(\d*)\.(\d*)\.(\d*))")

DefaultOptionsCallable = Callable[[Dict[str, Any]], None]


class Configuration(BaseModel):
    """
    docs

    """

    config_path: Path
    version_tag_pattern: Pattern = DEFAULT_VERSION_TAG_PATTERN
    news_fragments_directory: Path = DEFAULT_FRAGMENTS_DIR
    insert_marker: Pattern = re.compile(
        r"^(\s)*\.\. releaseherald_insert(\s)*$"
    )
    template: Path = Path(templates.__path__[0]) / "news.rst"
    unreleased: bool = False
    news_file: Path = Path("news.rst")
    target: Optional[Path] = None
    last_tag: str = ""
    latest: bool = False
    update: bool = True
    plugins: Optional[List[str]] = None

    class Config:
        paths_to_resolve: List[str] = ["template", "news_file"]
        default_options_callbacks: Dict[str, List[DefaultOptionsCallable]] = {
            "generate": []
        }
        extra = "allow"

    def as_default_options(self):
        default_options_callbacks: Dict[
            str, List[DefaultOptionsCallable]
        ] = self.__config__.default_options_callbacks

        result = defaultdict(dict)
        for command, callbacks in default_options_callbacks.items():
            for callback in callbacks:
                callback(result[command])

        return dict(result)

    @root_validator
    def resolve_paths(cls, values):
        config_path = Path(values["config_path"])
        root = config_path.parent if config_path.is_file() else config_path
        values = values.copy()
        for path_config in cls.__config__.paths_to_resolve:
            path = Path(values[path_config])
            values[path_config] = path if path.is_absolute() else root / path

        return values
