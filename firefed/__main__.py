from firefed import Session, util
from firefed.feature import Feature
from firefed.output import error, out, good
from firefed.util import fatal, read_profiles


def run():
    args = util.parse_args()
    if args.pop('show_profiles'):
        show_profiles()
        return
    session = Session(args.pop('profile'), verbosity=args.pop('verbosity'))
    ChosenFeature = Feature.feature_map()[args.pop('feature')]
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
