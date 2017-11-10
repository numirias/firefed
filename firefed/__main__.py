import argparse

from firefed import Firefed
from firefed.feature import Summary
from firefed.util import feature_map, profile_dir, ProfileNotFoundError
import firefed.__version__ as version


def profile_dir_type(dirname):
    try:
        return profile_dir(dirname)
    except ProfileNotFoundError as e:
        raise argparse.ArgumentTypeError(e)

def main():
    parser = argparse.ArgumentParser(
        'firefed',
        description=version.__description__,
    )
    parser.add_argument(
        '-p',
        '--profile',
        help='profile name or directory',
        type=profile_dir_type,
        default='',
    )
    parser.add_argument(
        '-s',
        '--summarize',
        action='store_true',
        help='summarize results',
    )
    subparsers = parser.add_subparsers(
        title='features',
        metavar='FEATURE',
        description='You must choose a feature.',
        dest='feature',
    )
    subparsers.required = True
    for name, Feature in feature_map().items():
        feature_parser = subparsers.add_parser(name, help=Feature.description)
        Feature.add_arguments(feature_parser)

    args = parser.parse_args()
    Firefed(args)


if __name__ == '__main__':
    main()
