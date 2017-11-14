from datetime import datetime
import os
from pathlib import Path
import pytest
import shutil
import sqlite3

from firefed import Firefed
from firefed.feature import Feature, Summary, Logins
from firefed.util import profile_dir, ProfileNotFoundError, feature_map, moz_datetime, moz_timestamp, make_parser


@pytest.fixture(scope='function')
def mock_home(tmpdir_factory):
    src_path = Path(__file__).parent / 'mock_home/mozilla'
    home_path = tmpdir_factory.mktemp('mock_home')
    profiles_ini = home_path / '.mozilla/firefox/profiles.ini'
    shutil.copytree(src_path, home_path.join('.mozilla'))
    with open(profiles_ini) as f:
        data = f.read().replace('$HOME', str(home_path))
    with open(profiles_ini, 'w') as f:
        f.write(data)
    return home_path

def mock_permissions(profile_dir):
    path = Path(profile_dir) / 'permissions.sqlite'
    con = sqlite3.connect(str(path))
    cursor = con.cursor()
    cursor.executescript('''
CREATE TABLE moz_perms ( id INTEGER PRIMARY KEY,origin TEXT,type TEXT,permission INTEGER,expireType INTEGER,expireTime INTEGER,modificationTime INTEGER);
INSERT INTO moz_perms VALUES(1,'http://one.example/','permission1',1,0,0,1461787589533);
INSERT INTO moz_perms VALUES(2,'https://two.example/','permission2',1,0,0,1461891431806);
INSERT INTO moz_perms VALUES(3,'https://three.example/','permission3',1,0,0,1462493666486);
    ''')

@pytest.fixture
def parser():
    return make_parser()


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


class TestFeatures:

    def test_permissions(self, mock_home, parser):
        config_path = mock_home / '.mozilla/firefox'
        profile_path = config_path / 'random.default'
        mock_permissions(profile_path)
        args = parser.parse_args(['--profile', str(profile_path), 'permissions', '--format', 'table'])
        Firefed(args)
