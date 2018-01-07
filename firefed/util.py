import argparse
from configparser import ConfigParser
from datetime import datetime
from itertools import chain
from pathlib import Path
import re

from attr import attrib, attrs

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
    parser.add_argument(
        '-f',
        '--force',
        help='force treating target as a profile directory even if it doesn\'t'
             ' look like one',
        action='store_true',
        default=False,
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
        for args, kwargs in feature.cli_args():
            feature_parser.add_argument(*args, **kwargs)
    return parser


def parse_args():
    parser = make_parser()
    return vars(parser.parse_args())


@attrs
class Tabulate:

    rows = attrib(converter=list)
    headers = attrib()
    maximums = attrib(init=False)

    def __attrs_post_init__(self):
        maxs = [0] * len(self.rows[0])
        for row in chain([self.headers], self.rows):
            for i, column in enumerate(row):
                maxs[i] = max(maxs[i], len(self.strip_invisible(column)))
        self.maximums = maxs

    def __call__(self):
        self.print_row(self.headers)
        self.print_row([''] * len(self.maximums), ch='-')
        for row in self.rows:
            self.print_row(row)

    def pad(self, s, num, ch):
        missing = num - len(self.strip_invisible(s))
        return s + missing * ch

    def print_row(self, row, ch=' '):
        print('  '.join([self.pad(c, self.maximums[i], ch) for i, c in
                         enumerate(row)]))

    @staticmethod
    def strip_invisible(s):
        invisibles = re.compile(r'\x1b\[\d*m')
        return re.sub(invisibles, '', s)


def tabulate(*args, **kwargs):
    Tabulate(*args, **kwargs)()
