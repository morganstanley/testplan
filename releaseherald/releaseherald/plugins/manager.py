from typing import Type, Dict

import pluggy

from releaseherald.plugins import hookspecs
from releaseherald.configuration import Configuration
from releaseherald.plugins.base import BasePlugin, BaseOutputPlugin
from releaseherald.plugins.latest_filter import LatestFilter
from releaseherald.plugins.metadata_extractor import FilenameMetadataExtractor
from releaseherald.plugins.submodules import Submodules

INTERNAL_PLUGINS: Dict[str, Type[object]] = {
    "base": BasePlugin,
    "base_output": BaseOutputPlugin,
    "filename_metadata_extractor": FilenameMetadataExtractor,
    "latest": LatestFilter,
    "submodules": Submodules,
}

DEFAULT_PLUGINS = ["filename_metadata_extractor", "latest", "submodules"]
SPECIAL_PLUGINS = ["base", "base_output"]


def get_pluginmanager(config: Configuration):
    pm = pluggy.PluginManager("releaseherald")
    pm.add_hookspecs(hookspecs)

    plugins = config.plugins
    if not plugins:
        plugins = DEFAULT_PLUGINS

    process_special_plugins(plugins)

    for plugin_name in reversed(plugins):
        if plugin_name in INTERNAL_PLUGINS:
            pm.register(INTERNAL_PLUGINS[plugin_name](), plugin_name)
        else:
            pm.load_setuptools_entrypoints("releaseherald_plugin", plugin_name)

    pm.hook.process_config(config=config)

    return pm


def process_special_plugins(plugins):
    for special_name in reversed(SPECIAL_PLUGINS):
        remove_string = f"-{special_name}"
        if remove_string in plugins:
            plugins.remove(remove_string)
        else:
            plugins.insert(0, special_name)
