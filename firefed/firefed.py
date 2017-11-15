from firefed.util import feature_map
from firefed.output import info


class Firefed:

    def __init__(self, args):
        self.profile_dir = args.profile
        ChosenFeature = feature_map()[args.feature]
        if args.format != 'csv': # TODO Refactor as verbosity flag
            info('Profile:', self.profile_dir)
            info('Feature: %s\n' % ChosenFeature.__name__)
        ChosenFeature(self)(args)
