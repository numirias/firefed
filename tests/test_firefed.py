import os
from pathlib import Path
import shutil
import pytest

from firefed.feature import Feature
from firefed.util import profile_dir, ProfileNotFoundError


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