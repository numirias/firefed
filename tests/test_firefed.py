import argparse
from datetime import datetime
import os
from pathlib import Path
import pytest
import shutil
import sqlite3
import csv
from io import StringIO
from unittest import mock
import sys

import firefed.__main__
from firefed import Firefed
from firefed.feature import Feature, Summary, Logins
from firefed.util import profile_dir, profile_dir_type, ProfileNotFoundError, feature_map, moz_datetime, moz_timestamp, make_parser


@pytest.fixture
def parser():
    return make_parser()

@pytest.fixture(scope='module')
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

@pytest.fixture(scope='module')
def mock_profile(mock_home):
    profile_path = mock_home / '.mozilla/firefox/random.default'
    make_permissions_sqlite(profile_path)
    return profile_path

@pytest.fixture(scope='function')
def feature(mock_profile, parser):
    def func(*more_args):
        args = parser.parse_args(['--profile', str(mock_profile), *more_args])
        Firefed(args)
    return func

def make_permissions_sqlite(profile_dir):
    path = Path(profile_dir) / 'permissions.sqlite'
    con = sqlite3.connect(str(path))
    cursor = con.cursor()
    cursor.executescript('''
CREATE TABLE moz_perms ( id INTEGER PRIMARY KEY,origin TEXT,type TEXT,permission INTEGER,expireType INTEGER,expireTime INTEGER,modificationTime INTEGER);
INSERT INTO moz_perms VALUES(1,'http://one.example/','permission1',1,0,0,1461787589533);
INSERT INTO moz_perms VALUES(2,'https://two.example/','permission2',1,0,0,1461891431806);
INSERT INTO moz_perms VALUES(3,'https://three.example/','permission3',1,0,0,1462493666486);
    ''')
    con.close()

def parse_csv(str_):
    return list(csv.reader(StringIO(str_)))


class TestMain:

    def test_main(self):
        with pytest.raises(SystemExit) as e:
            firefed.__main__.main()
        assert e.value.code == 2

    def test_main_help(self, capsys):
        with mock.patch.object(sys, 'argv', ['firefed', '-h']):
            with pytest.raises(SystemExit) as e:
                firefed.__main__.main()
        assert e.value.code == 0
        out, _ = capsys.readouterr()
        assert out.startswith('usage:')

    def test_main_with_feature(self, mock_profile):
        argv = ['firefed', '--profile', str(mock_profile), 'summary']
        with mock.patch.object(sys, 'argv', argv):
            firefed.__main__.main()


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

    def test_profile_dir_type(self, mock_home):
        assert profile_dir('default') == profile_dir_type('default')
        with pytest.raises(argparse.ArgumentTypeError):
            profile_dir_type('nonexistent')

    def test_argparse(self, capsys, mock_profile):
        parser = make_parser()
        with pytest.raises(SystemExit) as e:
            args = parser.parse_args(['-h'])
        assert e.value.code == 0
        out, _ = capsys.readouterr()
        assert out.startswith('usage:')
        args = parser.parse_args(['--profile', str(mock_profile), 'summary'])
        assert args.summarize is False

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

    def test_permissions(self, feature, capsys):
        feature('permissions', '--format', 'table')
        out, _ = capsys.readouterr()
        assert any('http://two.example/' and 'permission2' in line for line in out.split('\n'))
        feature('permissions', '--format', 'csv')
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert len(data) == 4
        assert data[0] == ['host', 'permission']
        assert ['https://two.example/', 'permission2'] in data
