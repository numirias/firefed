from firefed.util import feature_map
from firefed.output import info


class Session:

    def __init__(self, profile):
        self.profile = profile

    def __call__(self, feature, args={}):
        ChosenFeature = feature_map()[feature]
        if 'format' not in args or args['format'] != 'csv': # TODO Refactor as verbosity flag
            info('Profile:', self.profile)
            info('Feature: %s\n' % ChosenFeature.__name__)
        ChosenFeature(self, **args)()
