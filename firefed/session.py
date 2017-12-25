import logging
from firefed.output import logger, info
from firefed.util import feature_map


class Session:

    def __init__(self, profile, verbosity=0):
        self.profile = profile
        self.verbosity = verbosity
        if verbosity > 0:
            logger.setLevel(logging.INFO)

    def __call__(self, feature_name, feature_args=None):
        if feature_args is None:
            feature_args = {}
        ChosenFeature = feature_map()[feature_name]
        info('Profile: %s', self.profile)
        info('Feature: %s\n', ChosenFeature.__name__)
        ChosenFeature(self, **feature_args)()
