import os
import re

import pytest

from testplan.common.utils.parser import ArgMixin
from testplan.testing.listing import (
    ListingRegistry,
    listing_registry,
    NameLister,
    CountLister,
    ExpandedNameLister,
)


def test_defaults():
    assert len(listing_registry.listers) == 5
    arg_enum = listing_registry.to_arg()
    assert issubclass(arg_enum, ArgMixin)

    for enum in ["NAME", "NAME_FULL", "COUNT", "PATTERN", "PATTERN_FULL"]:
        assert arg_enum[enum]


def test_duplicate():
    registry = ListingRegistry()

    registry.add_lister(NameLister())
    assert len(registry.listers) == 1

    # let the enum creation handle the duplicate check for free
    registry.add_lister(NameLister())
    assert len(registry.listers) == 2

    with pytest.raises(TypeError):
        registry.to_arg()


def test_help_text():
    registry = ListingRegistry()
    registry.add_lister(CountLister())
    registry.add_lister(ExpandedNameLister())

    arg_enum = registry.to_arg()

    help_text = arg_enum.get_help_text(None).split(os.linesep)

    assert len(help_text) == 3  # the default + the two lister

    for help_line in help_text[1:]:
        match = re.match('"([^"]*)" - (.*)', help_line)
        assert match

        name, text = match.groups()
        lister = arg_enum.parse(name)
        assert lister

        assert lister.description() == text
