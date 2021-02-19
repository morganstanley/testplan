#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows how to display various data modelling techniques and their
associated statistics in Testplan. The models used are:

* linear regression
* classification
* clustering
"""
import os
import sys

from testplan import test_plan
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.suite import testsuite, testcase
from testplan.report.testing.styles import Style
from testplan.common.utils.timing import Timer

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score
import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plot
import numpy as np


# Create a Matplotlib scatter plot.
def create_scatter_plot(title, x, y, label, c=None):
    plot.scatter(x, y, c=c, label=label)
    plot.grid()
    plot.xlabel("x")
    plot.ylabel("y")
    plot.xlim((0, 1))
    plot.ylim((-2, 2))
    plot.title(title)


# Use the original docstring, formatting
# it using kwargs via string interpolation.

# e.g. `foo: {foo}, bar: {bar}`.format(foo=2, bar=5)` -> 'foo: 2, bar: 5'
def interpolate_docstring(docstring, kwargs):
    return docstring.format(**kwargs)


@testsuite
class ModelExamplesSuite(object):
    def setup(self, env, result):
        """
        Load the raw data from the CSV file.
        Log this data as a table in the report.
        """
        # Load the raw cosine data from the CSV file.

        self.x, self.y = np.loadtxt(
            os.path.join(os.path.dirname(__file__), "cos_data.csv"),
            delimiter=",",
            unpack=True,
            skiprows=1,
        )
        self.x_test = np.linspace(0, 1, 100)

        # Log it to display in the report, this will show the first 5 and last 5
        # rows if there are more than 10 rows.
        data = [["X", "y"]] + [
            [self.x[i], self.y[i]] for i in range(len(self.x))
        ]
        result.table.log(data, description="Raw cosine data")

    @testcase(
        parameters={"degrees": [2, 3, 4, 5, 10, 15]},
        docstring_func=interpolate_docstring,
    )
    def polynomial_regression(self, env, result, degrees):
        """
        Create and train a polynomial regression function with {degrees} degrees
        of freedom. Check if the Mean Square Error (MSE) and time to train the
        model are within their thresholds. Display the train data and the model
        on a plot.
        """
        # This example was based on
        # http://scikit-learn.org/stable/auto_examples/model_selection/plot_underfitting_overfitting.html

        # Create the pipeline to train a polynomial regression with varying
        # degrees of freedom.
        polynomial_features = PolynomialFeatures(
            degree=degrees, include_bias=False
        )
        pipeline = Pipeline(
            [
                ("polynomial_features", polynomial_features),
                ("linear_regression", LinearRegression()),
            ]
        )

        # Train the model and record how long this takes.
        timer = Timer()
        with timer.record("train_model"):
            pipeline.fit(self.x[:, np.newaxis], self.y)
        scores = cross_val_score(
            pipeline,
            self.x[:, np.newaxis],
            self.y,
            scoring="neg_mean_squared_error",
            cv=10,
        )

        # Check the Mean Square Error (MSE) and time to train the model are
        # within their thresholds.
        result.less(
            -scores.mean(),
            0.05,
            description="Mean Square Error threshold on test data",
        )
        result.less(
            timer["train_model"].elapsed,
            1,
            description="How long did the model take to train?",
        )

        # Display the train data and the model on a plot.
        create_scatter_plot(
            title="{} degrees of freedom model & Train data".format(degrees),
            x=self.x,
            y=self.y,
            label="Samples",
            c="black",
        )
        y_test = pipeline.predict(self.x_test[:, np.newaxis])
        plot.plot(self.x_test, y_test, label="Model")
        plot.legend(loc="best")
        result.matplot(plot)


# Hard-coding `pdf_path` and 'pdf_style' so that the downloadable example gives
# meaningful and presentable output. NOTE: this programmatic arguments passing
# approach will cause Testplan to ignore any command line arguments related to
# that functionality.
@test_plan(
    name="Basic Data Modelling Example",
    pdf_path=os.path.join(os.path.dirname(__file__), "report.pdf"),
    pdf_style=Style(passing="assertion-detail", failing="assertion-detail"),
)
def main(plan):
    """
    Testplan decorated main function to add and execute MultiTests.

    :return: Testplan result object.
    :rtype:  :py:class:`~testplan.base.TestplanResult`
    """
    model_examples = MultiTest(
        name="Model Examples", suites=[ModelExamplesSuite()]
    )
    plan.add(model_examples)


if __name__ == "__main__":
    sys.exit(not main())
