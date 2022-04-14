#!/usr/bin/env python
"""
This example shows usage of chart assertions.
"""
import os
import re
import sys
import random

from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


@testsuite
class SampleSuite:
    @testcase
    def line_tests(self, env, result):
        """
        Example from https://plotly.com/python/line-charts/
        """
        df = px.data.gapminder().query("continent=='Oceania'")
        fig = px.line(df, x="year", y="lifeExp", color="country")
        result.plotly(fig, description="Gapminder of Oceania")

    @testcase
    def timeline_tests(self, env, result):
        """
        Example from https://plotly.com/python/gantt/
        """
        df = pd.DataFrame(
            [
                dict(
                    Task="Job A",
                    Start="2009-01-01",
                    Finish="2009-02-28",
                    Completion_pct=50,
                ),
                dict(
                    Task="Job B",
                    Start="2009-03-05",
                    Finish="2009-04-15",
                    Completion_pct=25,
                ),
                dict(
                    Task="Job C",
                    Start="2009-02-20",
                    Finish="2009-05-30",
                    Completion_pct=75,
                ),
            ]
        )

        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Completion_pct",
        )
        fig.update_yaxes(autorange="reversed")

        result.plotly(fig, description="Task")

    @testcase
    def bar_tests(self, env, result):
        """
        Example from https://plotly.com/python/bar-charts/
        """
        months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=months,
                y=[20, 14, 25, 16, 18, 22, 19, 15, 12, 16, 14, 17],
                name="Primary Product",
                marker_color="indianred",
            )
        )
        fig.add_trace(
            go.Bar(
                x=months,
                y=[19, 14, 22, 14, 16, 19, 15, 14, 10, 12, 12, 16],
                name="Secondary Product",
                marker_color="lightsalmon",
            )
        )

        fig.update_layout(barmode="group", xaxis_tickangle=-45)
        result.plotly(fig, description="Rotated Bar Chart Labels")

    @testcase
    def pie_tests(self, env, result):
        """
        Example from https://plotly.com/python/pie-charts/
        """
        df = (
            px.data.gapminder()
            .query("year == 2007")
            .query("continent == 'Europe'")
        )
        df.loc[df["pop"] < 2.0e6, "country"] = "Other countries"
        fig = px.pie(
            df,
            values="pop",
            names="country",
            title="Population of European continent",
        )
        result.plotly(fig, description="Pie chart with plotly express")

    @testcase
    def scatter_tests(self, env, result):
        """
        Example from https://plotly.com/python/line-and-scatter/
        """
        df = px.data.iris()
        fig = px.scatter(
            df,
            x="sepal_width",
            y="sepal_length",
            color="species",
            size="petal_length",
            hover_data=["petal_width"],
        )
        result.plotly(fig, description="Set size and color with column names")

    @testcase
    def line_3d_tests(self, env, result):
        """
        Example from https://plotly.com/python/3d-line-plots/
        """
        rs = np.random.RandomState()
        rs.seed(0)

        def brownian_motion(T=1, N=100, mu=0.1, sigma=0.01, S0=20):
            dt = float(T) / N
            t = np.linspace(0, T, N)
            W = rs.standard_normal(size=N)
            W = np.cumsum(W) * np.sqrt(dt)  # standard brownian motion
            X = (mu - 0.5 * sigma ** 2) * t + sigma * W
            S = S0 * np.exp(X)  # geometric brownian motion
            return S

        dates = pd.date_range("2012-01-01", "2013-02-22")
        T = (dates.max() - dates.min()).days / 365
        N = dates.size
        start_price = 100
        y = brownian_motion(T, N, sigma=0.1, S0=start_price)
        z = brownian_motion(T, N, sigma=0.1, S0=start_price)

        fig = go.Figure(
            data=go.Scatter3d(
                x=dates,
                y=y,
                z=z,
                marker=dict(
                    size=4,
                    color=z,
                    colorscale="Viridis",
                ),
                line=dict(color="darkblue", width=2),
            )
        )

        fig.update_layout(
            width=800,
            height=700,
            autosize=False,
            scene=dict(
                camera=dict(
                    up=dict(x=0, y=0, z=1),
                    eye=dict(
                        x=0,
                        y=1.0707,
                        z=1,
                    ),
                ),
                aspectratio=dict(x=1, y=1, z=0.7),
                aspectmode="manual",
            ),
        )
        result.plotly(fig, description="Brownian Motion")


@test_plan(name="Charts Example")
def main(plan):
    plan.add(MultiTest(name="Chart Assertions Test", suites=[SampleSuite()]))


if __name__ == "__main__":
    sys.exit(not main())
