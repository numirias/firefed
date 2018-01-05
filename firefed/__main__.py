from firefed import Session, util
from firefed.feature import Feature


def main():
    args = util.parse_args()
    session = Session(args.pop('profile'), args.pop('verbosity'))
    feature = Feature.feature_map()[args.pop('feature')]
    feature(session, **args)()


if __name__ == '__main__':
    main()
