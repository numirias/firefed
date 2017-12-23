from firefed.util import feature_map
from firefed.output import info


class Session:

    def __init__(self, profile, verbosity=0):
        self.profile = profile
        self.verbosity = verbosity

    def __call__(self, feature, args=None):
        if args is None:
            args = {}
        ChosenFeature = feature_map()[feature]
        # TODO Refactor as verbosity level
        if 'format' not in args or args['format'] != 'csv':
            info('Profile:', self.profile)
            info('Feature: %s\n' % ChosenFeature.__name__)
        ChosenFeature(self, **args)()
