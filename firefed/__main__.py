import argparse
import os
import re
from firefed import Firefed
from feature import feature_map, Summary
import __version__ as version


def profile_dir(dirname):
    if dirname is None:
        dirname = 'default'
    if os.path.isdir(dirname):
        return dirname
    # If it's not an existing directory, try to find in local user profiles
    if re.match('^[\\w-]+$', dirname):
        home = os.path.expanduser('~/.mozilla/firefox')
        profile_names = os.listdir(home)
        for name in profile_names:
            if name.endswith('.%s' % dirname):
                return os.path.join(home, name)
    raise argparse.ArgumentTypeError('Profile %s not found.' % dirname)


def main():
    parser = argparse.ArgumentParser(
        'firefed',
        description=version.__description__,
    )
    parser.add_argument(
        '-p',
        '--profile',
        help='profile name or directory',
        type=profile_dir,
        default='default',
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
    for name, Feature in feature_map().items():
        feature_parser = subparsers.add_parser(name, help=Feature.description)
        Feature.add_arguments(feature_parser)

    args = parser.parse_args()
    Firefed(args)


if __name__ == '__main__':
    main()
