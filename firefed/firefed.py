from output import info


class Firefed:
    def __init__(self, args):
        self.profile_dir = args.profile
        info('Profile:', self.profile_dir)
        ChosenFeature = args.feature
        info('Feature: %s\n' % ChosenFeature.__name__)
        ChosenFeature(self)(args)
