import re
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Type

import parse
from pydantic import BaseModel

import releaseherald.plugins
from releaseherald.configuration import Configuration
from releaseherald.plugins.interface import VersionNews, News


class ParserType(str, Enum):
    RE = "re"
    PARSE = "parse"


class FilenameMetadataExtractorConfig(BaseModel):
    """
    Attributes:
        type: [re](https://github.com/r1chardj0n3s/parse#readme) or [parse](https://github.com/r1chardj0n3s/parse#readme)
        pattern: the pattern for the corresponding type, Should contains groups/fields
        target_attribute: if provided the resulting dictionary will be merged into that field of the metadata
    """

    type: ParserType
    pattern: str
    target_attribute: Optional[str]


CONFIG_ATTRIBUTE = "filename_metadata_extractor"


class Extractor(ABC):
    def __init__(self, pattern: str):
        pass

    @abstractmethod
    def match(self, text: str) -> Optional[Dict[str, str]]:
        ...


class RegexExtractor(Extractor):
    def __init__(self, pattern: str):
        super().__init__(pattern)
        self.pattern = re.compile(pattern)

    def match(self, text: str) -> Optional[Dict[str, str]]:
        match = self.pattern.match(text)
        if match:
            return match.groupdict()

        return None


class ParseExtractor(Extractor):
    def __init__(self, pattern: str):
        super().__init__(pattern)
        self.pattern = parse.compile(pattern)

    def match(self, text: str) -> Optional[Dict[str, str]]:
        result = self.pattern.parse(text)
        if result:
            return result.named

        return None


MATCHER_FACTORY_MAP: Dict[ParserType, Type[Extractor]] = {
    ParserType.RE: RegexExtractor,
    ParserType.PARSE: ParseExtractor,
}


class FilenameMetadataExtractor:
    def __init__(self):
        self.target_attribute: str = ""
        self.extractor: Optional[Extractor] = None

    @releaseherald.plugins.hookimpl
    def process_config(self, config: Configuration):

        extractor_config = config.parse_sub_config(
            CONFIG_ATTRIBUTE, FilenameMetadataExtractorConfig
        )

        if extractor_config:
            self.target_attribute = extractor_config.target_attribute
            self.extractor = MATCHER_FACTORY_MAP[extractor_config.type](
                extractor_config.pattern
            )

    @releaseherald.plugins.hookimpl
    def process_version_news(self, version_news: List[VersionNews]):
        if self.extractor is None:
            return

        for version in version_news:
            self.process_news_list(version.news)
            for submodule in version.submodule_news:
                self.process_news_list(submodule.news)

    def process_news_list(self, news_list: List[News]):
        for news in news_list:
            self.extend_news(news)

    def extend_news(self, news: News):
        if self.extractor is None:
            return

        metadata = self.extractor.match(Path(news.file_name).name)
        if metadata:
            target = news.metadata
            if self.target_attribute:
                target = news.metadata.setdefault(self.target_attribute, {})
            target.update(metadata)
