from testplan.common.utils.convert import sort_and_group
from testplan.common.utils.registry import Registry
from . import assertions
from .base import Group


class SummaryRegistry(Registry):
    """
    Records are done by class.__name__
    Lookups are done by `class_name` (str)
    """

    def get_category(self, obj):
        """No category defaults support for now"""
        return None

    def get_record_key(self, obj):
        return obj.__name__

    def get_lookup_key(self, obj):
        return obj

    def summarize(self, class_name, entries, limit):
        return self[class_name](entries, limit)


registry = SummaryRegistry()


@registry.bind_default()
def summarize_entries(category, class_name, passed, entries, limits):
    """
    Default summary function, just trims entries using the given ``limit``.
    """
    if passed:
        limit = limits["num_passing"]
    else:
        limit = limits["num_failing"]

    trimmed = entries[:limit]
    return Group(
        entries=trimmed,
        description=(
            "{category} - {class_name}"
            " - {pass_status} - Displaying"
            " {num_display} of {num_total}."
        ).format(
            category=category,
            class_name=class_name,
            pass_status="Passing" if passed else "Failing",
            num_display=len(trimmed),
            num_total=len(entries),
        ),
    )


def dict_failed_keys(table):
    """Returns all failed keys of the dict match comparison result table."""
    failed = []
    for _, key, result, _, _ in table:
        if key and result == "Failed":
            failed.append(key)
    return tuple(sorted(failed))


@registry.bind(assertions.DictMatch, assertions.FixMatch)
def summarize_dict_match(category, class_name, passed, entries, limits):
    """
    Summarized for FixMatch/DictMatch

    Uses default summary logic for passing entries, further groups failing
    entries by failed tags/keys.
    """
    if passed:
        return summarize_entries(category, class_name, passed, entries, limits)

    limit = limits["num_failing"]

    groups = sort_and_group(
        iterable=entries, key=lambda obj: dict_failed_keys(obj.comparison)
    )
    groups = [
        (key, group)
        for key, group, _ in sorted(
            [(k, g, len(g)) for k, g in groups],
            reverse=True,
            key=lambda x: x[2],
        )
    ]

    key_label = "key" if class_name == "DictMatch" else "tag"

    sub_groups = []

    for idx, entry in enumerate(groups):
        keys, entries = entry
        if idx >= limits["key_combs_limit"]:
            key_group = Group(
                entries=[
                    assertions.Fail("Total: {} failures.".format(len(entries)))
                ],
                description=("{key_label}s: {keys}").format(
                    key_label=key_label.title(), keys=", ".join(map(str, keys))
                ),
            )
        else:
            trimmed = entries[:limit]

            key_group = Group(
                entries=trimmed,
                description=(
                    "{key_label}s: {keys}"
                    " - (Displaying {num_display} of {num_total})"
                ).format(
                    key_label=key_label.title(),
                    keys=", ".join(map(str, keys)),
                    num_display=len(trimmed),
                    num_total=len(entries),
                ),
            )
        sub_groups.append(key_group)

    return Group(
        entries=sub_groups,
        description=(
            "Displaying failures for {num_groups}"
            " distinct {key_label} groups"
        ).format(key_label=key_label, num_groups=len(sub_groups)),
    )
