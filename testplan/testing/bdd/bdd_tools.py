import os
import re

from testplan.testing.bdd.suite import (
    GherkinTestSuiteBase,
    NonTestplanSafeNameError,
)

from boltons.iterutils import get_path

from testplan.testing.bdd.parsers import RegExParser
from testplan.testing.bdd.testloader import load_features
from testplan.testing.bdd.step_registry import StepRegistry

FEATURE_FILE_EXTENSION = ".feature"


class NoopContextResolver:
    def resolve(self, context, resolvable):
        return resolvable


class ContextResolver:
    def __init__(self, start_tag="{{", end_tag="}}"):
        self.start_tag = start_tag
        self.end_tag = end_tag

    @property
    def regexp(self):
        return (
            "({start_tag}((.(?!({start_tag}|{end_tag})))*.){end_tag})".format(
                start_tag=self.start_tag, end_tag=self.end_tag
            )
        )

    def resolve(self, context, text):
        result = text
        for marker, name, _, _ in re.findall(self.regexp, text):
            result = result.replace(
                marker, str(get_path(context, name, marker))
            )
        return result


BDD_CONTEXT_KEY = "__BDD_CONTEXT__"


def create_linked_registry(feature, default_parser_class):
    registry = StepRegistry()
    definition_file = "{}.steps.py".format(os.path.splitext(feature.file)[0])
    registry.load_steps(definition_file, default_parser_class)
    return registry


class BDDTestSuiteFactory:
    """
    Factory class which can create TestSuits from a directory of feature files

    :param features_path: is the path to the directory containing the feature and step definition
    :param resolver: context resolver can be used to refer context values from steps
    :param default_parser: the default parser used in step matching default use regex
    :param feature_linked_steps: assumes per feature step definition files
    :param common_step_dirs: list of paths to common step files
    """

    def __init__(
        self,
        features_path,
        resolver=NoopContextResolver(),
        default_parser=RegExParser,
        feature_linked_steps=False,
        common_step_dirs=None,
    ):

        self.features_path = features_path
        self.resolver = resolver
        self.default_step_parser_class = default_parser
        self.feature_linked_steps = feature_linked_steps
        features = load_features(features_path)
        self.common_step_dirs = common_step_dirs or []
        self.features = self._load_steps(features)

    def create_suites(self):
        """

        This is the factory function when can be used tyo obtain Multitest compatible TestSuites

        :return: a list of suites inherited from
            :py:class:`GherkinTestSuiteBase <testplan.testing.bdd.suite.GherkinTestSuiteBase>`.
        """

        suits = []
        for feature, step_registry in self.features:

            try:
                suite = self._create_suite(feature, step_registry)
                suits.append(suite)
            except NonTestplanSafeNameError as error:
                raise NonTestplanSafeNameError(
                    "{} in file: {}".format(str(error), feature.file)
                )
        return suits

    def _create_suite(self, feature, step_registry):

        suite = GherkinTestSuiteBase.get_suite_class(feature)(
            feature, step_registry, self.resolver
        )
        return suite

    def _load_steps(self, features):

        if self.feature_linked_steps:
            return [
                (
                    feature,
                    create_linked_registry(
                        feature, self.default_step_parser_class
                    ),
                )
                for feature in features
            ]
        else:
            registry = StepRegistry()

            steps_lookup_locations = [
                os.path.join(self.features_path, "steps")
            ]

            steps_lookup_locations.extend(self.common_step_dirs)

            for steps_location in steps_lookup_locations:
                for dirname, dirs, files in os.walk(steps_location):
                    for definition_file in [
                        os.path.join(dirname, featurefile)
                        for featurefile in files
                        if os.path.splitext(featurefile)[1] == ".py"
                    ]:
                        registry.load_steps(
                            definition_file, self.default_step_parser_class
                        )

            return [(feature, registry) for feature in features]
