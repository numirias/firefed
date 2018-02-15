from firefed import Session, util
from firefed.feature import Feature
from firefed.output import error, out, good
from firefed.util import fatal, read_profiles


def run():
    parser = util.make_parser()
    args = vars(parser.parse_args())
    if args.pop('show_profiles'):
        show_profiles()
        return
    feature_name = args.pop('feature')
    if feature_name is None:
        # Show help message end exit
        parser.parse_args(['-h'])
    try:
        profile = util.profile_dir(args.pop('profile'))
    except util.ProfileNotFoundError as e:
        fatal(e)
    session = Session(profile, verbosity=args.pop('verbosity'))
    ChosenFeature = Feature.feature_map()[feature_name]
    force = args.pop('force')
    feature = ChosenFeature(session, **args)
    if not feature.profile_path('times.json').exists() and not force:
        fatal('"%s" doesn\'t look like a profile directory. Use -f/--force if '
              'you insist it is.' % session.profile)
    feature()


def show_profiles():
    profiles = list(read_profiles())
    if not profiles:
        out('No local profiles found.')
        return
    out('%d profiles found:' % len(profiles))
    for profile in profiles:
        out('\n%s%s\n%s' % (
            profile.name,
            good(' [default]') if profile.default else '',
            profile.path,
        ))


def main():
    try:
        run()
    except util.FatalError as e:
        error(e)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
