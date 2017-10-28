from output import info
from feature.util import feature_map


class Firefed:

    def __init__(self, args):
        self.profile_dir = args.profile
        info('Profile:', self.profile_dir)
        ChosenFeature = feature_map()[args.feature]
        info('Feature: %s\n' % ChosenFeature.__name__)
        ChosenFeature(self)(args)
