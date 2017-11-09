import argparse
import configparser
import os
import re

from firefed import Firefed
from firefed.feature import feature_map, Summary
import firefed.__version__ as version


def profile_dir(dirname):
    if dirname is None:
        dirname = 'default'
    if os.path.isdir(dirname):
        return dirname
    mozilla_dir = os.path.expanduser('~/.mozilla/firefox')
    config = configparser.ConfigParser()
    config.read(os.path.join(mozilla_dir, 'profiles.ini'))
    profiles = [v for k, v in config.items() if k.startswith('Profile')]
    try:
        profile = next(p for p in profiles if p['name'] == dirname)
    except StopIteration:
        raise argparse.ArgumentTypeError('Profile "%s" not found.' % dirname)
    if profile['IsRelative']:
        path = os.path.join(mozilla_dir, profile['Path'])
        return path
    return profile['Path']


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
    subparsers.required = True
    for name, Feature in feature_map().items():
        feature_parser = subparsers.add_parser(name, help=Feature.description)
        Feature.add_arguments(feature_parser)

    args = parser.parse_args()
    Firefed(args)


if __name__ == '__main__':
    main()
