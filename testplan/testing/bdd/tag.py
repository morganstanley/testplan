import re
from dataclasses import dataclass
from typing import List

from testplan.testing.multitest import xfail


class XFailAdapter:
    def __init__(self, comment):
        self.comment = comment

    def apply(self, suite_or_case):
        return xfail(reason=self.comment, strict=True)(suite_or_case)


@dataclass
class TagParams:
    xfail: XFailAdapter = None
    execution_group: str = None


class TagProcessor:
    def process_tags(
        self, tags: List[str], tag_params: TagParams
    ) -> List[str]:
        return tags


class XFailTagProcessor(TagProcessor):
    KNOWN_TO_FAIL_REGEX = re.compile(
        r"^KNOWN_TO_FAIL(([^:/]+)/)?([^:]+)?:?(.*)$"
    )

    def process_tag(self, tag: str) -> XFailAdapter:
        match = self.KNOWN_TO_FAIL_REGEX.match(tag)
        if match:
            return XFailAdapter(comment=match.group(4))

    def process_tags(
        self, tags: List[str], tag_params: TagParams
    ) -> List[str]:
        super().process_tags(tags, tag_params)

        new_tags = []
        for tag in tags:
            adapter = self.process_tag(tag)
            if adapter:
                tag_params.xfail = adapter
                tag = "KNOWN_TO_FAIL"

            new_tags.append(tag)
        return new_tags


class ExecutionGroupTagProcessor(TagProcessor):
    REGEX = re.compile(r"^TP_EXECUTION_GROUP:(\S*?)$")

    def process_tags(
        self, tags: List[str], tag_params: TagParams
    ) -> List[str]:
        new_tags = []

        for tag in tags:
            match = self.REGEX.match(tag)
            if match:
                tag_params.execution_group = match.group(1)
                # do not add the tag it is just passing information
            else:
                new_tags.append(tag)

        return new_tags


def apply_tag_processors(
    tags: List[str], processors: List[TagProcessor], tag_params: TagParams
) -> List[str]:
    for processor in processors:
        tags = processor.process_tags(tags, tag_params)

    return tags
