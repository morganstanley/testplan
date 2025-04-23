import re
from collections import defaultdict
from pathlib import Path
from typing import Pattern, List, Callable, Dict, Any, Optional, Type, TypeVar

from pydantic import BaseModel, root_validator

from releaseherald import templates

DEFAULT_FRAGMENTS_DIR = Path("news_fragments")

DEFAULT_VERSION_TAG_PATTERN = re.compile(r"(?P<version>(\d*)\.(\d*)\.(\d*))")

DefaultOptionsCallable = Callable[[Dict[str, Any]], None]

MODEL = TypeVar("MODEL", bound=BaseModel)


class Configuration(BaseModel):
    """
    This class represent the configuration read from the config file.
    See attribute details in [Configuration](../configuration.md)
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

    def parse_sub_config(
        self, attribute_name: str, sub_config_model: Type[MODEL]
    ) -> MODEL:
        """
        Helper for plugin developers to parse a section of the config with the passed model, and replace the
        dictionary with the model object

        Args:
            attribute_name: the attribute holding the plugin config
            sub_config_model: the model describe the sub config

        Returns:
            an instance of the parsed config

        """
        config = getattr(self, attribute_name, None)
        parsed_config = sub_config_model.parse_obj(config) if config else None
        setattr(self, attribute_name, parsed_config)
        return parsed_config

    def resolve_path(self, path: Path) -> Path:
        """
        Helper function for plugin developers to resolve relative paths in config that supposed to be relative to this
        config file

        Args:
            path: the path to resolve

        Returns:
            an absolute path

        """
        root = _config_root(self.config_path)
        return _resolve_path(root, path)

    @root_validator
    def resolve_paths(cls, values):
        config_path = Path(values["config_path"])
        root = _config_root(config_path)
        values = values.copy()
        for path_config in cls.__config__.paths_to_resolve:
            path = Path(values[path_config])
            values[path_config] = _resolve_path(root, path)

        return values


def _config_root(config_path: Path):
    return config_path.parent if config_path.is_file() else config_path


def _resolve_path(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path
