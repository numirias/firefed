import os
from pathlib import Path
import shutil
import pytest
from datetime import datetime

from firefed.feature import Feature, Summary
from firefed.util import profile_dir, ProfileNotFoundError, feature_map, moz_datetime, moz_timestamp


@pytest.fixture(scope='function')
def mock_home(tmpdir_factory):
    src_path = Path(__file__).parent / 'mock_home/mozilla'
    dst_home_path = tmpdir_factory.mktemp('mock_home')
    dst_profiles_ini = dst_home_path / '.mozilla/firefox/profiles.ini'
    shutil.copytree(src_path, dst_home_path.join('.mozilla'))
    with open(dst_profiles_ini) as f:
        data = f.read().replace('$HOME', str(dst_home_path))
    with open(dst_profiles_ini, 'w') as f:
        f.write(data)
    return dst_home_path


class TestUtils:

    def test_profile_dir(self, monkeypatch, mock_home):
        print(mock_home)
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

    def test_feature_map(self):
        fmap = feature_map()
        assert len(fmap) > 1
        assert fmap['summary'] is Summary

    def test_timestamps(self):
        ts = moz_timestamp(1000000)
        assert ts == 1
        dt = moz_datetime(1000000)
        assert dt == datetime.fromtimestamp(1)
