#!/usr/bin/env python
"""
This example shows how to display various data modelling techniques and their
associated statistics in Testplan. The models used are:

* linear regression
* classification
* clustering
"""

import os
import sys
import random

from testplan import test_plan
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.suite import testsuite, testcase
from testplan.report.testing.styles import Style

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, classification_report
from sklearn.cluster import KMeans
from sklearn import datasets, linear_model, svm

import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plot
import numpy as np


def create_scatter_plot(title, x, y, x_label, y_label, c=None):
    plot.scatter(x, y, c=c)
    plot.grid()
    plot.xlabel(x_label)
    plot.ylabel(y_label)
    plot.title(title)


def create_image_plot(title, img_data, rows, columns, index):
    plot.subplot(rows, columns, index)
    plot.axis("off")
    plot.imshow(img_data, cmap=plot.cm.gray_r, interpolation="nearest")
    plot.title(title)


@testsuite
class ModelExamplesSuite:
    @testcase
    def basic_linear_regression(self, env, result):
        """
        This example was based on:
        http://scikit-learn.org/stable/auto_examples/linear_model/plot_ols.html.
        Train a basic linear regression model on BMI and the likelihood of
        diabetes. In the report, record:
         * coefficients
         * mean squared error
         * variance
         * plot of the regression with the test data
        """
        # Gather and separate the data into features (X) and results (y). We are
        # only using the BMI feature to compare against likelihood of diabetes.
        diabetes = datasets.load_diabetes()
        X = diabetes.data[:, np.newaxis, 2]
        y = diabetes.target
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2
        )

        # Train the linear regression model and make predictions.
        regr = linear_model.LinearRegression()
        regr.fit(X_train, y_train)
        diabetes_y_pred = regr.predict(X_test)

        # Log the statistics to the report.
        mse = mean_squared_error(y_test, diabetes_y_pred)
        r2 = r2_score(y_test, diabetes_y_pred)
        result.log("Coefficients: {}".format(regr.coef_))
        result.log("Mean squared error: {0:.2f}".format(mse))
        result.log("Variance: {0:.2f}".format(r2))

        # Plot the predictions and display this plot on the report.
        create_scatter_plot(
            "Basic Linear Regression Example",
            X_test,
            y_test,
            "BMI (kg/m^2)",
            "Likelihood of diabetes",
            "black",
        )
        plot.plot(X_test, diabetes_y_pred, color="blue", linewidth=3)
        result.matplot(plot)

    @testcase
    def basic_classifier(self, env, result):
        """
        This example was based on:
        http://scikit-learn.org/stable/auto_examples/classification/plot_digits_classification.html#sphx-glr-auto-examples-classification-plot-digits-classification-py.
        Train a basic classifier to classify hand drawn numbers. In the report,
        record:
         * precision per class
         * recall per class
         * f1-score per class
         * support per class
         * some example images with the predicted and actual classes
        """
        # Gather and split the data into features (X) and results (y). We
        # reshape each of the digit images from an 8x8 array into a 64x1 array.
        digits = datasets.load_digits()
        n_samples = len(digits.images)
        data = digits.images.reshape((n_samples, -1))
        X_train, X_test, y_train, y_test = train_test_split(
            data, digits.target, test_size=0.2
        )

        # Train the classifier and make predictions.
        classifier = svm.SVC(gamma=0.001)
        classifier.fit(X_train, y_train)
        predicted = classifier.predict(X_test)

        # Log the precision, recall, f1 and supports statistics (within the
        # classification report) to the report. Show four range images from the
        # test set with their predictions and actual values.
        result.log(classification_report(y_test, predicted))
        for i, sample in enumerate(random.sample(range(0, len(y_test)), 3)):
            t = "Prediction: {}\nActual: {}".format(
                predicted[sample], y_test[sample]
            )
            create_image_plot(t, X_test[sample].reshape((8, 8)), 1, 3, i + 1)
        result.matplot(plot, 4, 3)

    @testcase
    def basic_k_means_cluster(self, env, result):
        """
        Train a basic k means cluster on some randomly generated blobs of data.
        In the report, record:
         * the number of clusters
         * the plot of the clusters
        """
        # Create random data blobs and train a K-Means cluster to group this
        # data into 3 clusters.
        n_clusters = 3
        random_state = 100
        X, y = datasets.make_blobs(n_samples=1500, random_state=random_state)
        clusterer = KMeans(n_clusters=n_clusters, random_state=random_state)
        y_pred = clusterer.fit_predict(X)

        # Log the number of clusters and plot the clustered data.
        result.log("Number of clusters: {}".format(n_clusters))
        create_scatter_plot(
            "Basic K-Means Cluster Example",
            X[:, 0],
            X[:, 1],
            "Feature 1",
            "Feature 2",
            c=y_pred,
        )
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
