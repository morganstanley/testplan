import argparse


class ReportTagsAction(argparse.Action):
    """
    Argparse action for parsing multiple report tag
    arguments, builds up a list of dictionary of sets.

    In:

    .. code-block:: bash

        --report-tags foo bar hello=world --report-tags one two color=red

    Out:

    .. code-block:: python

        [
            {
                'simple': {'foo', 'bar'},
                'hello': {'world'}
            },
            {
                'simple': {'one', 'two'},
                'color': {'red'},
            }
        ]
    """

    def __call__(self, parser, namespace, values, option_string=None):
        from testplan.testing import tagging

        items = getattr(namespace, self.dest) or []

        tag_arg = [tagging.parse_tag_arguments(v) for v in values]
        tag_arg = tagging.merge_tag_dicts(*tag_arg)

        items.append(tag_arg)

        setattr(namespace, self.dest, items)


class CustomReportFilterAction(argparse.Action):
    """
    Argparse action serving higher-precedence shortcuts for report filters.
    """

    MUTEX_DESTS = ["reporting_filter", "omit_passed", "omit_skipped"]

    def __init__(self, filter_rep: str, *args, **kwargs):
        self.filter_rep = filter_rep
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if any(
            getattr(namespace, dest)
            for dest in self.MUTEX_DESTS
            if dest != self.dest
        ):
            parser.error(
                f'argument "{option_string}" not allowed with other report '
                f'filter argument "{self.option_strings[0]}"'
            )
        setattr(namespace, "reporting_filter", self.filter_rep)
        setattr(namespace, "reporting_filter_preserve_structure", True)

    @staticmethod
    def use_filter(filter_rep: str):
        return lambda *args, **kwargs: CustomReportFilterAction(
            filter_rep, *args, **kwargs
        )
