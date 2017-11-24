import argparse
from collections import namedtuple
import csv
from datetime import datetime
from io import StringIO
from pathlib import Path
import pytest

from firefed import Session
from firefed.feature import Feature, output_formats, sqlite_data, argument, Permissions, Forms, Bookmarks, History, Downloads, Hosts, InputHistory, Visits, Cookies, Addons, Logins, Preferences, Infect, Summary
from firefed.feature.feature import NotMozLz4Exception
from firefed.feature.cookies import Cookie, session_file
from firefed.util import profile_dir


def parse_csv(str_):
    return list(csv.reader(StringIO(str_)))

class TestFeature:

    def test_argument(self, mock_session):
        @argument('-f', '--foo')
        class SomeFeature(Feature):
            def run(self):
                pass
        assert SomeFeature(mock_session, foo='x').foo == 'x'

    def test_default_arguments(self, mock_session):
        @argument('-f', '--foo', default='x')
        class SomeFeature(Feature):
            def run(self):
                pass
        assert SomeFeature(mock_session).foo == 'x'

    def test_output_formats(self, mock_session):
        @output_formats(['a', 'b', 'c'], default='b')
        class SomeFeature(Feature):
            def run(self):
                pass
        assert SomeFeature(mock_session, format='c').format == 'c'
        assert SomeFeature(mock_session).format == 'b'

    def test_init(self, MockFeature, mock_session):
        feature = MockFeature(mock_session)
        assert feature._defaults == {}

    def test_run(self, mock_session):
        has_run = False
        class SomeFeature(Feature):
            def run(self):
                nonlocal has_run
                has_run = True
        feature = SomeFeature(mock_session)
        feature()
        assert has_run
        assert 'summary' not in feature._defaults

    def test_summarize(self, mock_session):
        has_prepared = has_run = has_summarized = False
        class SomeFeature(Feature):
            def run(self):
                nonlocal has_run
                has_run = True
            def summarize(self):
                nonlocal has_summarized
                has_summarized = True
        SomeFeature(mock_session, summary=True)()
        assert not has_run
        assert has_summarized

        feature = SomeFeature(mock_session)
        feature()
        assert 'summary' in feature._defaults

    def test_prepare(self, mock_session):
        has_prepared = has_run = False
        class SomeFeature(Feature):
            def prepare(self):
                nonlocal has_prepared
                has_prepared = True
                return 'somedata'
            def run(self, data):
                nonlocal has_run
                has_run = True
                assert data == 'somedata'
        SomeFeature(mock_session)()
        assert has_prepared
        assert has_run

    def test_wrong_argument(self, mock_session, MockFeature):
        with pytest.raises(TypeError):
            MockFeature(mock_session, unknown_argument=1)()

    def test_profile_path(self, MockFeature):
        session = Session(profile='/foo/bar')
        feature = MockFeature(session)
        assert feature.profile_path('baz') == Path('/foo/bar/baz')

    def test_loading(self, mock_feature):
        assert mock_feature.load_json('test_json.json')['foo']['bar'] == 2

        Foo = namedtuple('Foo', 'c1 c2')
        foos = mock_feature.load_sqlite('test_sqlite.sqlite', 't1', Foo)
        assert Foo(c1='r1v1', c2='r1v2') in foos

        assert mock_feature.load_mozlz4('test_mozlz4.lz4') == b'foo'
        with pytest.raises(NotMozLz4Exception):
            mock_feature.load_mozlz4('test_json.json')

    def test_exec_sqlite(self, mock_feature):
        res = mock_feature.exec_sqlite('test_sqlite.sqlite', 'SELECT c2 from t1')
        assert ('r2v2',) in res

    def test_build_format(self, MockFeature, mock_session):
        res = None
        @output_formats(['foo'])
        class MockFeatureFoo(MockFeature):
            def build_foo(self, arg):
                nonlocal res
                res = arg
        MockFeatureFoo(mock_session, format='foo').build_format(arg='baz')
        assert res == 'baz'

    def test_sqlite_data(self, mock_session):
        data = None
        class SomeFeature(Feature):
            @sqlite_data(db='test_sqlite.sqlite', table='t1', columns=['c1', 'c2'])
            def run(self, data_):
                nonlocal data
                data = data_
        SomeFeature(mock_session)()
        assert ('r1v1', 'r1v2') in data

        class SomeFeature2(Feature):
            @sqlite_data(db='nonexistent.sqlite', table='t1', columns=['c1', 'c2'])
            def run(self, data):
                pass
        with pytest.raises(FileNotFoundError):
            SomeFeature2(mock_session)()

class TestSmallFeatures:

    def test_downloads(self, mock_session, capsys):
        Downloads(mock_session)()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert 'file:///foo/bar' in lines
        assert 'nodownload' not in lines

    def test_hosts(self, mock_session, capsys):
        Hosts(mock_session)()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert 'two.example' in lines

    def test_input_history(self, mock_session, capsys):
        InputHistory(mock_session)()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert 'bar' in lines

    def test_forms(self, mock_session, capsys):
        Forms(mock_session)()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert 'ccc=ddd' in lines

class TestPermissionsFeature:

    def test_formats(self, mock_session, capsys):
        Permissions(mock_session, format='table')()
        out, _ = capsys.readouterr()
        assert ['https://two.example/', 'permission2'] in (line.split() for line in out.split('\n'))
        Permissions(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert len(data) == 4
        assert data[0] == ['host', 'permission']
        assert ['https://two.example/', 'permission2'] in data

class TestHistoryFeature:

    def test_formats(self, mock_session, capsys):
        History(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert len(data) == 4
        assert data[0] == ['url', 'title', 'last_visit_date', 'visit_count']
        assert ['http://two.example/', 'two', '2', '200'] in data

        History(mock_session, format='list')()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert 'http://two.example/' in lines
        assert '    Visits:     200' in lines

        History(mock_session, format='short')()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert 'http://one.example/' in lines

class TestVisitsFeature:

    def test_formats(self, mock_session, capsys):
        Visits(mock_session, format='list')()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert '%s %s' % (datetime.fromtimestamp(1), 'http://one.example/') in lines

        Visits(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert data[0] == ['id', 'from_visit', 'visit_date', 'url']
        assert ['1', '2', '1', 'http://one.example/']

class TestCookiesFeature:

    def test_single_cookie(self):
        cookie = Cookie(name='foo', value='bar')
        assert str(cookie) == 'foo=bar'

        cookie = Cookie(name='foo', value='bar', host='one.example', path='/baz', secure=True, http_only=True)
        assert all(x in str(cookie).lower() for x in ['foo=bar', 'path=/baz', 'secure', 'httponly', 'domain=one.example'])

    def test_cookies(self, mock_session, capsys):
        Cookies(mock_session, format='list')()
        out, _ = capsys.readouterr()
        assert any(line.startswith('k1=v1') for line in out.split('\n'))

        feature = Cookies(mock_session)
        cookies = feature.load_ss_cookies('sessionstore.jsonlz4')
        assert any((c.name, c.value, c.host) == ('sk2', 'sv2', 'two.example') for c in cookies)

        Cookies(mock_session, host='tw*.example', format='list')()
        out, _ = capsys.readouterr()
        assert out.startswith('k2=v2')

        assert session_file('sessionstore') == session_file('sessionstore.jsonlz4')
        assert session_file('sessionstore') != session_file('nonexistent')

        Cookies(mock_session, session_file='nonexistent', format='list')()
        out, _ = capsys.readouterr()
        assert 'not found' in out

        Cookies(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert ['k1', 'v1', 'one.example', '/', '1', '0'] in data

class TestBookmarksFeature:

    def test_formats(self, mock_session, capsys):
        Bookmarks(mock_session, format='list')()
        out, _ = capsys.readouterr()
        assert 'bookmark in level2' in out.split('\n')

        Bookmarks(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert ['bookmark in level2', 'http://two.example/', '5', '55'] in data

        Bookmarks(mock_session, format='tree')()
        out, _ = capsys.readouterr()
        assert 'http://one.example' in out
        # TODO Tests could be improved, esp. for tree output

class TestAddonsFeature:

    def test_formats(self, mock_session, capsys):
        Addons(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert data[0] == ['id', 'name', 'version', 'enabled', 'signed', 'visible']
        assert ['foo@bar', 'fooextension', '1.2.3', 'True', 'preliminary', 'True'] in data
        assert ['bar@baz', 'barextension', '0.1rc', 'False', '', 'False'] in data

        Addons(mock_session, format='list')()
        out, _ = capsys.readouterr()
        assert out.startswith('fooextension')
        assert all(x in out for x in ['preliminary', '[enabled]'])

        Addons(mock_session, format='table')()
        out, _ = capsys.readouterr()
        assert 'fooextension' in out
        assert 'barextension' in out

    def test_addons_by_id(self, mock_session, capsys):
        Addons(mock_session, format='csv', id='foo@bar')()
        out, _ = capsys.readouterr()
        assert 'fooextension' in out
        assert 'barextension' not in out

    def test_addons_errors(self, mock_session):
        # Can't check outdated without version
        with pytest.raises(SystemExit) as e:
            Addons(mock_session, format='table', outdated=True)()
        assert e.value.code == 1

        # Can't check outdated if not list format
        with pytest.raises(SystemExit) as e:
            Addons(mock_session, format='list', outdated=True)()
        assert e.value.code == 1
        # TODO Add --outdated tests

class TestLoginsFeature:

    def test_formats(self, mock_session, capsys):
        Logins(mock_session, master_password='master', format='table')()
        out, _ = capsys.readouterr()
        assert all(x in out for x in ['foo', 'bar'])

        Logins(mock_session, master_password='master', format='list')()
        out, _ = capsys.readouterr()
        assert all(x in out for x in ['foo', 'bar'])

        Logins(mock_session, master_password='master', format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert ['http://one.example', 'foo', 'bar'] in data

    def test_no_libnss(self, mock_session, capsys):
        with pytest.raises(SystemExit) as e:
            Logins(mock_session, libnss='nonexistent', format='csv')()
        out, _ = capsys.readouterr()
        assert e.value.code == 1
        assert 'Can\'t open libnss' in out

    def test_pw_prompt(self, mock_session, capsys, monkeypatch):
        import getpass
        monkeypatch.setattr('getpass.getpass', lambda *args, **kwargs: 'master')
        Logins(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        assert 'foo' in out

    def test_wrong_pw(self, mock_session, capsys):
        with pytest.raises(SystemExit) as e:
            Logins(mock_session, master_password='wrong', format='csv')()
        out, _ = capsys.readouterr()
        assert e.value.code == 1
        assert 'Incorrect master password' in out

class TestPreferencesFeature:

    def test_preferences(self, mock_session, capsys):
        Preferences(mock_session)()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert 'foo.bar = false' in lines
        assert 'baz = 123' in lines
        assert 'abc = "def"' in lines
        # TODO More feature tests

class TestInfectFeature:

    def test_check(self, mock_session, capsys):
        Infect(mock_session, want_check=True)()
        out, _ = capsys.readouterr()
        assert 'doesn\'t seem fully installed' in out
        # TODO More feature tests

class TestSummaryFeature:

    def test_summary(self, mock_session, capsys):
        Summary(mock_session)()
        out, _ = capsys.readouterr()
        assert 'custom preferences found' in out
        assert out.count('\n') == 1
