from typing import List

from git import Tag, Repo
from icecream import ic  # type: ignore

import releaseherald.plugins
from releaseherald.configuration import Configuration


class DemoPlugin:

    def __init__(self):
        self.config: Configuration = None

    @releaseherald.plugins.hookimpl
    def process_config(self, config: Configuration):
        self.config = config
        ic(config)

    @releaseherald.plugins.hookimpl
    def process_tags(self, repo: Repo, tags: List[Tag]):
        ic(tags)


plugin = DemoPlugin()