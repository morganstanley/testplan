import os

from .gherkin import Feature

FEATURE_FILE_EXTENSION = ".feature"


def load_features(features_path):
    featurefiles = []
    for dirname, dirs, files in os.walk(features_path):
        featurefiles.extend(
            [
                os.path.join(dirname, featurefile)
                for featurefile in files
                if os.path.splitext(featurefile)[1] == FEATURE_FILE_EXTENSION
            ]
        )

    return [Feature(featurefile) for featurefile in featurefiles]
