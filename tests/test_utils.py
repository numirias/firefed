import argparse
from datetime import datetime
import os

import pytest

from firefed.util import (ProfileNotFoundError, make_parser, moz_datetime,
                          moz_to_unix_timestamp, profile_dir, profile_dir_type,
                          tabulate)


class TestUtils:

    def test_profile_dir(self, monkeypatch, mock_home):
        config_path = mock_home / '.mozilla/firefox'
        default_profile_path = config_path / 'random.default'
        monkeypatch.setitem(os.environ, 'HOME', str(mock_home))
        assert profile_dir('default') == default_profile_path
        assert profile_dir(default_profile_path) == default_profile_path
        assert profile_dir('') == default_profile_path
        assert profile_dir(None) == default_profile_path
        assert profile_dir('user2') == config_path / 'random.user2'
        with pytest.raises(ProfileNotFoundError):
            profile_dir('nonexistent')

        assert profile_dir('default') == profile_dir_type('default')
        with pytest.raises(argparse.ArgumentTypeError):
            profile_dir_type('nonexistent')

    def test_argparse(self, capsys, mock_profile):
        parser = make_parser()
        with pytest.raises(SystemExit) as e:
            parser.parse_args(['-h'])
        assert e.value.code == 0
        out, _ = capsys.readouterr()
        assert out.startswith('usage:')

    def test_timestamps(self):
        ts = moz_to_unix_timestamp(1000000)
        assert ts == 1
        dt = moz_datetime(1000000)
        assert dt == datetime.fromtimestamp(1)

    def test_tabulate(self, capsys):
        rows = [
            ('r1c1', 'r1c2_'),
            ('r2c1__', 'r2c2'),
        ]
        headers = ['c1', 'c2']
        tabulate(rows, headers)
        out, _ = capsys.readouterr()
        assert out == (
            'c1      c2   \n'
            '------  -----\n'
            'r1c1    r1c2_\n'
            'r2c1__  r2c2 \n')


# TODO write proper tests for make_parser (argument names, etc.)
