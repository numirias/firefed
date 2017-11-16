from pathlib import Path
from pytest import fixture
import shutil
import sqlite3
import lz4

from firefed import Session
from firefed.feature import Feature
from firefed.util import make_parser


def make_test_sqlite(profile_dir):
    path = Path(profile_dir) / 'test_sqlite.sqlite'
    con = sqlite3.connect(str(path))
    cursor = con.cursor()
    cursor.executescript('''
    CREATE TABLE t1 (c1, c2);
    INSERT INTO t1 VALUES('r1v1', 'r1v2');
    INSERT INTO t1 VALUES('r2v1', 'r2v2');
    ''')
    con.close()

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

def make_test_moz_lz4(profile_dir):
    path = Path(profile_dir) / 'test_moz_lz4.lz4'
    compressed = lz4.block.compress(b'foo')
    with open(path, 'wb') as f:
        f.write(b'mozLz40\0' + compressed)

@fixture
def parser():
    return make_parser()

@fixture(scope='module')
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

@fixture(scope='module')
def mock_profile(mock_home):
    profile_path = mock_home / '.mozilla/firefox/random.default'
    make_permissions_sqlite(profile_path)
    make_test_sqlite(profile_path)
    make_test_moz_lz4(profile_path)
    return profile_path

@fixture
def mock_session(mock_profile):
    return Session(mock_profile)

@fixture
def mock_feature(mock_session, MockFeature):
    return MockFeature(mock_session)

@fixture
def MockFeature():
    class MockFeature(Feature):
        def run(self):
            pass
    return MockFeature
