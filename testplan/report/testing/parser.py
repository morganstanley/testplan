import argparse


class ReportTagsAction(argparse.Action):
    """
        Argparse action for parsing multiple report tag
        arguments, builds up a list of dictionary of sets.

        In:
            --report-tags foo bar hello=world --report-tags one two color=red

        Out:

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
