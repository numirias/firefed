# flake8: noqa
import json
from pathlib import Path
import re
import shutil
import sqlite3

import lz4.block
from pytest import fixture

from firefed import Session
from firefed.feature import Feature
from firefed.util import make_parser


def write_data_to(data, path):
    with open(path, 'w') as f:
        f.write(data)

def profile_file(func):
    func._profile_file = True
    return func


@profile_file
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

@profile_file
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

@profile_file
def make_formhistory_sqlite(profile_dir):
    path = Path(profile_dir) / 'formhistory.sqlite'
    con = sqlite3.connect(str(path))
    cursor = con.cursor()
    cursor.executescript('''
    CREATE TABLE moz_formhistory (id INTEGER PRIMARY KEY, fieldname TEXT NOT NULL, value TEXT NOT NULL, timesUsed INTEGER, firstUsed INTEGER, lastUsed INTEGER, guid TEXT);
    INSERT INTO moz_formhistory VALUES(3,'aaa','bbb',70,1461722880950000,1496016155338000,'guid1');
    INSERT INTO moz_formhistory VALUES(7,'ccc','ddd',68,1462027382316000,1510013515062000,'guid2');
    ''')
    con.close()

@profile_file
def make_places_sqlite(profile_dir):
    path = Path(profile_dir) / 'places.sqlite'
    con = sqlite3.connect(str(path))
    cursor = con.cursor()
    cursor.executescript('''
    CREATE TABLE moz_places (id, url, title, visit_count, last_visit_date);
    INSERT INTO moz_places VALUES(1, 'http://one.example/', 'one', 100, 1000000);
    INSERT INTO moz_places VALUES(2, 'http://two.example/', 'two', 200, 2000000);
    INSERT INTO moz_places VALUES(3, 'http://three.example/', 'three', 300, 3000000);

    CREATE TABLE moz_annos (anno_attribute_id, dateAdded, content);
    INSERT INTO moz_annos VALUES(10, 1000000, 'file:///foo/bar');
    INSERT INTO moz_annos VALUES(12, 2000000, 'nodownload');
    INSERT INTO moz_annos VALUES(10, 3000000, 'file:///baz');

    CREATE TABLE moz_hosts (host);
    INSERT INTO moz_hosts VALUES('one.example');
    INSERT INTO moz_hosts VALUES('two.example');

    CREATE TABLE moz_inputhistory (input);
    INSERT INTO moz_inputhistory VALUES('foo');
    INSERT INTO moz_inputhistory VALUES('bar');

    CREATE TABLE moz_historyvisits (id, from_visit, visit_date, place_id);
    INSERT INTO moz_historyvisits VALUES(1, 2, 1000000, 1);
    INSERT INTO moz_historyvisits VALUES(2, 0, 1000000, 2);

    CREATE TABLE moz_bookmarks (id, parent, type, fk, title, guid, dateAdded, lastModified);
    INSERT INTO moz_bookmarks VALUES(1, 0, 2, 0, '', 'root________', 1000000, 11000000);
    INSERT INTO moz_bookmarks VALUES(2, 1, 2, 0, 'rootfolder', 'guid2', 3000000, 33000000);
    INSERT INTO moz_bookmarks VALUES(3, 2, 1, 1, 'bookmark in rootfolder', 'guid3', 2000000, 22000000);
    INSERT INTO moz_bookmarks VALUES(4, 2, 2, 0, 'level2', 'guid4', 4000000, 44000000);
    INSERT INTO moz_bookmarks VALUES(5, 4, 1, 2, 'bookmark in level2', 'guid5', 5000000, 55000000);
    INSERT INTO moz_bookmarks VALUES(6, 4, 1, 3, '', 'guid6', 6000000, 66000000);
    ''')
    con.close()

@profile_file
def make_cookies_sqlite(profile_dir):
    path = Path(profile_dir) / 'cookies.sqlite'
    con = sqlite3.connect(str(path))
    cursor = con.cursor()
    cursor.executescript('''
    CREATE TABLE moz_cookies (name, value, host, path, isSecure, isHttpOnly, sameSite, expiry);
    INSERT INTO moz_cookies VALUES('k1', 'v1', 'one.example', '/', 1, 0, 0, 1000);
    INSERT INTO moz_cookies VALUES('k2', 'v2', 'two.example', '/p2', 0, 1, 1, 449410533679);
    ''')

@profile_file
def make_test_mozlz4(profile_dir):
    path = Path(profile_dir) / 'test_mozlz4.lz4'
    compressed = lz4.block.compress(b'foo')
    with open(path, 'wb') as f:
        f.write(b'mozLz40\0' + compressed)

@profile_file
def make_sessionstore_jsonlz4(profile_dir):
    path = Path(profile_dir) / 'sessionstore.jsonlz4'
    data = {
        'cookies': [
            {
                'name': 'sk1',
                'value': 'sv1',
                'host': 'one.example',
            },
            {
                'name': 'sk2',
                'value': 'sv2',
                'host': 'two.example',
            },
        ]
    }
    json_bytes = bytes(json.dumps(data), 'utf-8')
    compressed = lz4.block.compress(json_bytes)
    with open(path, 'wb') as f:
        f.write(b'mozLz40\0' + compressed)

@profile_file
def make_addon_startup_jsonlz4(profile_dir):
    path = Path(profile_dir) / 'addonStartup.json.lz4'
    data = {
        'app-system-defaults': {
            'path': '/foo',
            'addons': {
                'foo@bar': {
                    'path': 'bar',
                    'enabled': True,
                },
            }
        }
    }
    json_bytes = bytes(json.dumps(data), 'utf-8')
    compressed = lz4.block.compress(json_bytes)
    with open(path, 'wb') as f:
        f.write(b'mozLz40\0' + compressed)

@profile_file
def make_extensions_json(profile_dir):
    path = Path(profile_dir) / 'extensions.json'
    data = {
        'addons': [
            {
                'id': 'foo@bar',
                'defaultLocale': {
                    'name': 'fooextension',
                },
                'version': '1.2.3',
                'active': True,
                'signedState': 1,
                'visible': True,
                'location': 'app-profile',
                'type': 'type1',
                'path': '/foo/bar',
            },
            {
                'id': 'bar@baz',
                'defaultLocale': {
                    'name': 'barextension',
                },
                'version': '0.1rc',
                'active': False,
                'visible': False,
                'location': 'app-profile',
                'type': 'type2',
                'path': '/bar/baz',
            },
            {
                'id': '3@three',
                'defaultLocale': {
                    'name': 'extension3',
                },
                'version': 'three',
                'active': True,
                'signedState': 0,
                'visible': True,
                'location': 'app-profile',
                'type': 'type3',
                'path': '/abc',
            },
        ],
    }
    with open(path, 'w') as f:
        f.write(json.dumps(data))

@profile_file
def make_logins_json(profile_dir):
    path = Path(profile_dir) / 'logins.json'
    data = {
        "logins": [
            {
                "id": 1,
                "hostname": "http://one.example",
                "formSubmitURL": "http://one.example",
                "usernameField": "username",
                "passwordField": "password",
                "encryptedUsername": "MDIEEPgAAAAAAAAAAAAAAAAAAAEwFAYIKoZIhvcNAwcECA55nTfQgZCkBAgL7cdTHY5pyQ==",
                "encryptedPassword": "MDIEEPgAAAAAAAAAAAAAAAAAAAEwFAYIKoZIhvcNAwcECLByVk//ztL9BAj2IUeTu9MZvA==",
                "encType": 1,
                "timeCreated": 1000000,
                "timeLastUsed": 11000000,
                "timePasswordChanged": 111000000,
                "timesUsed": 2
            },
        ],
    }
    with open(path, 'w') as f:
        f.write(json.dumps(data))

@profile_file
def make_addons_json(profile_dir):
    path = Path(profile_dir) / 'addons.json'
    data = {
        "schema": 5,
        "addons": [
            {
                "id": "foo@bar",
                "name": "fooextension",
                "type": "type1",
                "version": "1.2.3",
            }
        ]
    }
    with open(path, 'w') as f:
        f.write(json.dumps(data))

@profile_file
def make_times_json(profile_dir):
    path = Path(profile_dir) / 'times.json'
    data = {"created": 1000}
    with open(path, 'w') as f:
        f.write(json.dumps(data))


@profile_file
def make_prefs_js(profile_dir):
    data = '''
    user_pref("foo.bar", false);
    user_pref("baz", 123);
    user_pref("abc", "def");
    user_pref("beacon.enabled", true);
    '''
    write_data_to(data, Path(profile_dir) / 'prefs.js')
    data = '''
    user_pref("foo.bar", false);
    user_pref("baz", 456);
    user_pref("userkey", "userval");
    user_pref("browser.search.region", "US");
    user_pref("goodkey", "goodval");
    '''
    write_data_to(data, Path(profile_dir) / 'user.js')

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
    for func in globals().values():
        if not getattr(func, '_profile_file', False):
            continue
        func(profile_path)
    return profile_path

@fixture(scope='module')
def mock_empty_profile(mock_home):
    profile_path = mock_home / '.mozilla/firefox/random.user2'
    return profile_path

@fixture
def mock_session(mock_profile):
    return Session(mock_profile)

@fixture
def mock_feature(mock_session, MockFeature):
    return MockFeature(mock_session)

@fixture(scope='function')
def MockFeature():
    from attr import attrs
    @attrs
    class MockFeature(Feature):
        def run(self):
            pass
    return MockFeature

@fixture
def match():
    def match(*args, **kwargs):
        return re.match(*args, **kwargs)
    return match

@fixture
def stdout(capsys):
    def func():
        out, _ = capsys.readouterr()
        return out
    return func

@fixture
def stderr(capsys):
    def func():
        _, err = capsys.readouterr()
        return err
    return func

@fixture
def stdouterr(capsys):
    return capsys.readouterr
