from configparser import ConfigParser
import os
from collections import OrderedDict
from datetime import datetime
from pathlib import Path


class ProfileNotFoundError(Exception):

    def __init__(self, name):
        super().__init__('Profile "%s" not found.' % name)


def profile_dir(val):
    """Return directory for dirname.
    """
    if val:
        possible_path = Path(val)
        if possible_path.exists():
            return possible_path
    mozilla_dir = Path('~/.mozilla/firefox').expanduser()
    config = ConfigParser()
    config.read(mozilla_dir / 'profiles.ini')
    profiles = [v for k, v in config.items() if k.startswith('Profile')]
    try:
        if val:
            print('looking for name', val)
            profile = next(p for p in profiles if p['name'] == val)
        else:
            print('looking for default')
            profile = next(p for p in profiles if 'Default' in p and p['Default'])
    except StopIteration:
        raise ProfileNotFoundError(val or '(default)')
    profile_path = Path(profile['Path'])
    if profile['IsRelative']:
        return mozilla_dir / profile_path
    return profile_path


def feature_map():
    from firefed.feature import Feature
    return OrderedDict(
        sorted((m.__name__.lower(), m) for m in Feature.__subclasses__())
    )


def moz_datetime(ts):
    return datetime.fromtimestamp(moz_timestamp(ts))


def moz_timestamp(ts):
    return ts // 1000000
