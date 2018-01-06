import argparse
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path

import firefed.__version__ as version


class ProfileNotFoundError(Exception):

    def __init__(self, name):
        super().__init__('Profile "%s" not found.' % name)


def profile_dir(name):
    """Return path to FF profile for a given profile name or path."""
    if name:
        possible_path = Path(name)
        if possible_path.exists():
            return possible_path
    mozilla_dir = Path('~/.mozilla/firefox').expanduser()
    config = ConfigParser()
    config.read(mozilla_dir / 'profiles.ini')
    profiles = [v for k, v in config.items() if k.startswith('Profile')]
    try:
        if name:
            profile = next(p for p in profiles if p['name'] == name)
        else:
            profile = next(p for p in profiles if 'Default' in p and
                           int(p['Default']))
    except StopIteration:
        raise ProfileNotFoundError(name or '(default)')
    profile_path = Path(profile['Path'])
    if int(profile['IsRelative']):
        return mozilla_dir / profile_path
    return profile_path


def moz_datetime(ts):
    """Convert Mozilla timestamp to datetime."""
    return datetime.fromtimestamp(moz_to_unix_timestamp(ts))


def moz_to_unix_timestamp(ts):
    """Convert Mozilla timestamp to Unix timestamp."""
    try:
        return ts // 1000000
    except TypeError:
        return 0


def profile_dir_type(dirname):
    try:
        return profile_dir(dirname)
    except ProfileNotFoundError as e:
        raise argparse.ArgumentTypeError(e)


def make_parser():
    from firefed.feature import Feature
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
        '-v',
        '--verbose',
        help='verbose output (can be used multiple times)',
        action='count',
        dest='verbosity',
        default=0,
    )
    subparsers = parser.add_subparsers(
        title='features',
        metavar='FEATURE',
        description='You must choose a feature.',
        dest='feature',
    )
    subparsers.required = True
    for name, feature in Feature.feature_map().items():
        feature_parser = subparsers.add_parser(name,
                                               help=feature.description())
        for attrib_name, arg in feature.cli_args.items():
            kwargs = arg.kwargs
            kwargs['dest'] = attrib_name
            feature_parser.add_argument(*arg.args, **kwargs)
    return parser


def parse_args():
    parser = make_parser()
    return vars(parser.parse_args())
