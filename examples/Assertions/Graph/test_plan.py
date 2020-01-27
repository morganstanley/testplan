"""
These examples show usage of graphs
"""
import sys
import os

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class SampleSuite(object):

    # Basic graphing for singe series graphing:
    @testcase
    def graph_tests(self, env, result):

        # The last 3 arguments don't have to be keyword, however for clarity they are included.
        # A Basic single series line graph, where the line has been specified to be red,
        # and the axis have been labelled
        result.graph(
            "Line",
            {
                "Data Name": [
                    {"x": 0, "y": 8},
                    {"x": 1, "y": 5},
                    {"x": 2, "y": 4},
                    {"x": 3, "y": 9},
                    {"x": 4, "y": 1},
                    {"x": 5, "y": 7},
                    {"x": 6, "y": 6},
                    {"x": 7, "y": 3},
                    {"x": 8, "y": 2},
                    {"x": 9, "y": 0},
                ]
            },
            description="Line Graph",
            series_options={"Data Name": {"colour": "red"}},
            graph_options={"xAxisTitle": "Time", "yAxisTitle": "Failures"},
        )

        # A Basic single series scatter graph, where the points have been specified to be black
        result.graph(
            "Scatter",
            {
                "Data Name": [
                    {"x": 0, "y": 8},
                    {"x": 1, "y": 50},
                    {"x": 2, "y": 4},
                    {"x": -10, "y": 9},
                    {"x": 4, "y": 1},
                    {"x": 5, "y": 7},
                    {"x": 6, "y": -3},
                    {"x": 7, "y": 3},
                    {"x": 100, "y": 2},
                    {"x": 9, "y": 0},
                ]
            },
            description="Scatter Graph",
            series_options={"Data Name": {"colour": "black"}},
            graph_options=None,
        )

        # A single series Bar Graph, with no colour or graph preference, so a random colour will be assigned
        result.graph(
            "Bar",
            {
                "Any Name You Want": [
                    {"x": "A", "y": 10},
                    {"x": "B", "y": 5},
                    {"x": "C", "y": 15},
                ]
            },
            description="Bar Graph",
            series_options=None,
            graph_options=None,
        )

        # A single series Hexbin series, with no options specified
        result.graph(
            "Hexbin",
            {
                "Data Name": [
                    {"x": 0, "y": 8},
                    {"x": 1, "y": 5},
                    {"x": 2, "y": 4},
                    {"x": 3, "y": 9},
                    {"x": 4, "y": 1},
                    {"x": 5, "y": 7},
                    {"x": 6, "y": 6},
                    {"x": 7, "y": 3},
                    {"x": 8, "y": 2},
                    {"x": 9, "y": 0},
                ]
            },
            description="Hexbin Graph",
            series_options=None,
            graph_options=None,
        )

        # A Whisker graph where the data structure expects an 'xVariance' and 'yVariance' to produce the whiskers
        result.graph(
            "Whisker",
            {
                "Data Name": [
                    {"x": 1, "y": 10, "xVariance": 0.5, "yVariance": 2},
                    {"x": 1.7, "y": 12, "xVariance": 1, "yVariance": 1},
                    {"x": 2, "y": 5, "xVariance": 0, "yVariance": 0},
                    {"x": 3, "y": 15, "xVariance": 0, "yVariance": 2},
                    {"x": 2.5, "y": 7, "xVariance": 0.25, "yVariance": 2},
                    {"x": 1.8, "y": 7, "xVariance": 0.25, "yVariance": 1},
                ]
            },
            description="Whisker Graph",
            series_options=None,
            graph_options=None,
        )

        # A simple contour graph. Note: the data structure is simply (x, y) coordinates
        result.graph(
            "Contour",
            {
                "Data Name": [
                    {"x": 0, "y": 8},
                    {"x": 1, "y": 50},
                    {"x": 2, "y": 4},
                    {"x": -10, "y": 9},
                    {"x": 4, "y": 1},
                    {"x": 5, "y": 7},
                    {"x": 6, "y": -3},
                    {"x": 7, "y": 3},
                    {"x": 100, "y": 2},
                    {"x": 9, "y": 0},
                ]
            },
            description="Contour Graph",
            series_options=None,
            graph_options=None,
        )

        # A simple Pie chart. Note: the colour can be set as 'literal' to make the colour
        # the same as that specified in the data structure
        result.graph(
            "Pie",
            {
                "Data Name": [
                    {"angle": 1, "color": "#89DAC1", "name": "Car"},
                    {"angle": 2, "color": "#F6D18A", "name": "Bus"},
                    {"angle": 5, "color": "#1E96BE", "name": "Train"},
                    {"angle": 3, "color": "#DA70BF", "name": "Bicycle"},
                    {"angle": 5, "color": "#F6D18A", "name": "Walking"},
                ]
            },
            description="Pie Chart",
            series_options={"Data Name": {"colour": "literal"}},
            graph_options=None,
        )

    # Some examples of multi series graphs:
    @testcase
    def multiseries_graph_tests(self, env, result):

        # This line graph has two data series 'graph 1' and 'graph 2' and will be plot on the same axis
        # NOTE: with multi series graphs you will often want the legend to be set to true
        # The series options have set the first data set to be red, and the second to be blue
        result.graph(
            "Line",
            {
                "graph 1": [
                    {"x": 0, "y": 8},
                    {"x": 1, "y": 5},
                    {"x": 2, "y": 4},
                    {"x": 3, "y": 9},
                    {"x": 4, "y": 1},
                    {"x": 5, "y": 7},
                    {"x": 6, "y": 6},
                    {"x": 7, "y": 3},
                    {"x": 8, "y": 2},
                    {"x": 9, "y": 0},
                ],
                "graph 2": [
                    {"x": 1, "y": 3},
                    {"x": 2, "y": 5},
                    {"x": 3, "y": 15},
                    {"x": 4, "y": 12},
                ],
            },
            description="Line Graph",
            series_options={
                "graph 1": {"colour": "red"},
                "graph 2": {"colour": "blue"},
            },
            graph_options={
                "xAxisTitle": "Time",
                "yAxisTitle": "Volume",
                "legend": True,
            },
        )

        # This is a multi series bar graph, data with the same 'x' values in
        # different data series will be plotted next to each other
        result.graph(
            "Bar",
            {
                "Bar 1": [
                    {"x": "A", "y": 10},
                    {"x": "B", "y": 5},
                    {"x": "C", "y": 15},
                ],
                "Bar 2": [
                    {"x": "A", "y": 3},
                    {"x": "B", "y": 6},
                    {"x": "C", "y": 15},
                    {"x": "D", "y": 12},
                ],
            },
            description="Bar Graph",
            series_options={
                "Bar 1": {"colour": "green"},
                "Bar 2": {"colour": "purple"},
            },
            graph_options={"legend": True},
        )


# PDF style must be 'assertion-detail' to view
# non-assertion related detail like graphs or logs
@test_plan(
    name="Assertions Example",
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
    pdf_path=os.path.join(os.path.dirname(__file__), "report.pdf"),
    pdf_style=Style(passing="assertion-detail", failing="assertion-detail"),
)
def main(plan):
    plan.add(MultiTest(name="Graph Assertions Test", suites=[SampleSuite()]))


if __name__ == "__main__":
    sys.exit(not main())
