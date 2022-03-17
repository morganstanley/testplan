import pluggy

from releaseherald.plugins import hookspecs
from releaseherald.configuration import Configuration
from releaseherald.plugins.latest_filter import LatestFilter
from releaseherald.plugins.base import BasePlugin
from releaseherald.plugins.metadata_extractor import FilenameMetadataExtractor
from releaseherald.plugins.submodules import Submodules


def get_pluginmanager(config: Configuration):
    pm = pluggy.PluginManager("releaseherald")
    pm.add_hookspecs(hookspecs)
    pm.register(BasePlugin())
    pm.register(Submodules())
    pm.register(LatestFilter())
    pm.register(FilenameMetadataExtractor())

    pm.hook.process_config(config=config)

    return pm
