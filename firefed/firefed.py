from firefed.util import feature_map
from firefed.output import info


class Firefed:

    def __init__(self, args):
        self.profile_dir = args.profile
        info('Profile:', self.profile_dir)
        ChosenFeature = feature_map()[args.feature]
        info('Feature: %s\n' % ChosenFeature.__name__)
        ChosenFeature(self)(args)
