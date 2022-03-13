import pluggy

from releaseherald.plugins import hookspecs
from releaseherald.configuration import Configuration
from releaseherald.plugins.base import BasePlugin


def get_pluginmanager(config: Configuration):
    pm = pluggy.PluginManager("releaseherald")
    pm.add_hookspecs(hookspecs)
    pm.register(BasePlugin())

    pm.hook.process_config(config=config)

    return pm

