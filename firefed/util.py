import argparse
from configparser import ConfigParser
from datetime import datetime
from itertools import chain
from pathlib import Path
import re

from attr import attrib, attrs

import firefed.__version__ as version


CONFIG_PATH = '~/.mozilla/firefox'
PROFILES_INI = 'profiles.ini'


@attrs
class Profile:
    name = attrib()
    path = attrib()
    default = attrib(default=False, converter=lambda x: bool(int(x)))


class ProfileNotFoundError(Exception):

    def __init__(self, name):
        if name is None:
            text = 'No default profile found. Use --profile to specify one.'
        else:
            text = 'Profile "%s" not found.' % name
        super().__init__(text)


class FatalError(Exception):
    """Raised when an unrecoverable error in a feature occurs."""
    pass


def fatal(text):
    raise FatalError(text)


def mozilla_dir():
    return Path(CONFIG_PATH).expanduser()


def read_profiles():
    config = ConfigParser()
    config.read(str(mozilla_dir() / PROFILES_INI))
    for section, profile in config.items():
        if not section.startswith('Profile'):
            continue
        path = Path(profile.get('Path'))
        if int(profile['IsRelative']):
            path = Path(mozilla_dir() / path)
        yield Profile(profile.get('Name'), path, profile.get('Default', 0))


def profile_dir(name):
    """Return path to FF profile for a given profile name or path."""
    if name:
        possible_path = Path(name)
        if possible_path.exists():
            return possible_path
    profiles = list(read_profiles())
    try:
        if name:
            profile = next(p for p in profiles if p.name == name)
        else:
            profile = next(p for p in profiles if p.default)
    except StopIteration:
        raise ProfileNotFoundError(name)
    return profile.path


def moz_datetime(ts):
    """Convert Mozilla timestamp to datetime."""
    return datetime.fromtimestamp(moz_to_unix_timestamp(ts))


def moz_to_unix_timestamp(ts):
    """Convert Mozilla timestamp to Unix timestamp."""
    try:
        return ts // 1000000
    except TypeError:
        return 0


def make_parser():
    from firefed.feature import Feature
    parser = argparse.ArgumentParser(
        'firefed',
        description=version.__description__,
    )
    parser.add_argument(
        '-P',
        '--profiles',
        help='show all local profiles',
        action='store_true',
        dest='show_profiles',
    )
    parser.add_argument(
        '-p',
        '--profile',
        help='profile name or directory to be used when running a feature',
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
        help='treat target as a profile directory even if it doesn\'t'
             ' look like one',
        action='store_true',
        default=False,
    )
    subparsers = parser.add_subparsers(
        title='features',
        metavar='FEATURE',
        description='Set the feature you want to run as positional argument. '
        'Each feature has its own sub arguments which can be listed with '
        '`firefed <feature> -h`.',
        dest='feature',
    )
    for name, feature in Feature.feature_map().items():
        feature_parser = subparsers.add_parser(name,
                                               help=feature.description())
        for args, kwargs in feature.cli_args():
            feature_parser.add_argument(*args, **kwargs)
    return parser


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
