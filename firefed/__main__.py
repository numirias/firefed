import argparse
import os
import re
from firefed import Firefed
from feature import feature_map, Summary


def feature_type(val):
    try:
        return feature_map()[val]
    except KeyError as key:
        raise argparse.ArgumentTypeError(
            'Feature %s not found. Choose from: {%s}' %
            (key, ', '.join(feature_map())))


def profile_dir(dirname):
    if dirname is None:
        dirname = 'default'
    if os.path.isdir(dirname):
        return dirname
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
        description=
        'Firefed is a Firefox profile analyzer focusing on privacy and security.',
    )
    parser.add_argument(
        '-p',
        '--profile',
        help='profile name or directory',
        type=profile_dir,
        default='default')
    parser.add_argument(
        '-f',
        '--feature',
        type=feature_type,
        default=Summary,
        help='{%s}' % ', '.join(feature_map()))
    parser.add_argument(
        '-s', '--summarize', action='store_true', help='summarize results')
    args = parser.parse_args()
    Firefed(args)


if __name__ == '__main__':
    main()
