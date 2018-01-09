from firefed import Session, util
from firefed.feature import Feature
from firefed.output import fatal


def main():
    args = util.parse_args()
    session = Session(args.pop('profile'), verbosity=args.pop('verbosity'))
    ChosenFeature = Feature.feature_map()[args.pop('feature')]
    force = args.pop('force')
    feature = ChosenFeature(session, **args)
    if not feature.profile_path('times.json').exists() and not force:
        fatal('"%s" doesn\'t look like a profile directory. Use -f/--force if '
              'you insist it is.' % session.profile)
    feature()


if __name__ == '__main__':
    main()
