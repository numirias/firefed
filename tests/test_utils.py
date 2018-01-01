import argparse
from datetime import datetime
import pytest
import os


from firefed.feature import Feature, Summary
from firefed.util import profile_dir, profile_dir_type, ProfileNotFoundError, \
    feature_map, moz_datetime, moz_timestamp, make_parser


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

    def test_feature_map(self):
        fmap = feature_map()
        assert len(fmap) > 1
        assert fmap['summary'] is Summary
        assert Feature not in fmap.values()

    def test_timestamps(self):
        ts = moz_timestamp(1000000)
        assert ts == 1
        dt = moz_datetime(1000000)
        assert dt == datetime.fromtimestamp(1)


# TODO write proper tests for make_parser (argument names, etc.)
