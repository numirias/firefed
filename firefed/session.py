import logging
from firefed.output import log, logger
from firefed.util import feature_map


class Session:

    def __init__(self, profile, verbosity=0):
        self.profile = profile
        self.verbosity = verbosity
        if verbosity > 0:
            logger.setLevel(logging.INFO)

    def __call__(self, feature, args=None):
        if args is None:
            args = {}
        ChosenFeature = feature_map()[feature]
        log('Profile: %s', self.profile)
        log('Feature: %s\n', ChosenFeature.__name__)
        ChosenFeature(self, **args)()
