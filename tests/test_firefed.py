import csv
import os
import re
import subprocess
import time
from datetime import datetime
from io import StringIO
from pathlib import Path
from socket import AF_INET, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET, socket
from textwrap import dedent

import attr
import pytest
from attr import attrs
from firefed import Session
from firefed.feature import (Addons, Bookmarks, Cookies, Downloads, Feature,
                             Forms, History, Hosts, Infect, InputHistory,
                             Logins, Permissions, Preferences, Summary, Visits,
                             arg, formatter)
from firefed.feature.cookies import Cookie, session_file_type
from firefed.feature.feature import NotMozLz4Error
from firefed.feature.preferences import Preference
from firefed.util import FatalError
from pytest import mark


def parse_csv(s):
    return list(csv.reader(StringIO(s)))


def nomarkup(s):
    return re.sub(r'\x1b\[\d*m', '', s)


class TestFeature:

    def test_run(self, mock_session):
        has_run = has_summarized = False
        @attrs
        class SomeFeature(Feature):
            def run(self):
                nonlocal has_run
                has_run = True
            def summarize(self):
                nonlocal has_summarized
                has_summarized = True
        SomeFeature(mock_session)()
        assert has_run
        assert not has_summarized

    def test_summarize(self, mock_session):
        has_run = has_summarized = False
        @attrs
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

    def test_prepare(self, mock_session):
        has_prepared = has_run = False
        @attrs
        class SomeFeature(Feature):
            def prepare(self):
                nonlocal has_prepared
                has_prepared = True
                return 'somedata'
            def run(self):
                nonlocal has_run
                has_run = True
            def summarize(self):
                pass
        SomeFeature(mock_session)()
        assert has_prepared
        assert has_run

    def test_arguments(self, mock_session, MockFeature):
        @attrs
        class SomeFeature(MockFeature):
            my_arg1 = arg('-a', '--arg1')
            my_arg2 = arg('-b', '--arg2')
        assert SomeFeature(mock_session, my_arg1='x').my_arg1 == 'x'
        assert SomeFeature(mock_session, my_arg1='x').my_arg2 is None

    def test_default_arguments(self, mock_session, MockFeature):
        @attrs
        class SomeFeature(MockFeature):
            my_foo = arg('-f', '--foo', default=2)
        assert SomeFeature(mock_session).my_foo == 2

    def test_wrong_argument(self, mock_session, MockFeature):
        with pytest.raises(TypeError):
            MockFeature(unknown_argument=1)

    def test_feature_map(self):
        fmap = Feature.feature_map()
        assert len(fmap) > 1
        assert fmap['summary'] is Summary
        assert Feature not in fmap.values()

    def test_formatters(self, mock_session, MockFeature):
        @attrs
        class SomeFeature(MockFeature):
            @formatter('a')
            def x(self):
                pass
            @formatter('b', default=True)
            def y(self):
                pass
            @formatter('c')
            def z(self):
                pass
        assert SomeFeature(mock_session, format='c').format == 'c'
        assert SomeFeature(mock_session).format == 'b'

    def test_formatters_no_default(self, mock_session, MockFeature):
        @attrs
        class SomeFeature(MockFeature):
            @formatter('a')
            def x(self):
                pass
        assert SomeFeature(mock_session).format is None

    def test_build_format(self, MockFeature, mock_session):
        has_run = False
        @attrs
        class SomeFeature(MockFeature):
            @formatter('a')
            def x(self):
                nonlocal has_run
                has_run = True
        SomeFeature(mock_session, format='a').build_format()
        assert has_run

    def test_description(self, MockFeature):
        class SomeFeature(Feature):
            """A description.

            More Text."""
        class SomeFeature2(Feature):
            pass
        assert SomeFeature.description() == 'A description.'
        assert SomeFeature2.description() == '(no description)'

    def test_has_summary(self, MockFeature):
        class F1(MockFeature):
            pass
        class F2(MockFeature):
            def summarize(self):
                pass
        assert not F1.summarizable()
        assert F2.summarizable()

    def test_all_csvs(self, mock_session, capsys):
        """All features with a CSV formatter should be CSV-parseable."""
        for Feature_ in Feature.feature_map().values():
            if 'csv' in Feature_.formatters():
                kwargs = {'password': 'master'} if Feature_ is Logins else {}
                Feature_(mock_session, format='csv', **kwargs)()
                out, _ = capsys.readouterr()
                parse_csv(out)


class TestFeatureHelpers:

    def test_profile_path(self, MockFeature):
        session = Session(profile=Path('/foo/bar'))
        feature = MockFeature(session)
        assert feature.profile_path('baz') == Path('/foo/bar/baz')

        with pytest.raises(FileNotFoundError, match='nonexistent'):
            feature.profile_path('nonexistent', must_exist=True)

    def test_load_json(self, mock_feature):
        assert mock_feature.load_json('test_json.json')['foo']['bar'] == 2

    def test_load_sqlite(self, mock_feature):
        Foo = attr.make_class('Foo', ['c1', 'c2'])
        foos = mock_feature.load_sqlite(
            'test_sqlite.sqlite',
            table='t1',
            cls=Foo,
        )
        assert Foo(c1='r1v1', c2='r1v2') in foos

    def test_load_sqlite_with_column_map(self, mock_feature):
        Foo = attr.make_class('Foo', ['obj_c1', 'c2'])
        foos = mock_feature.load_sqlite(
            'test_sqlite.sqlite',
            table='t1',
            cls=Foo,
            column_map={'c1': 'obj_c1'},
        )
        assert Foo(obj_c1='r1v1', c2='r1v2') in foos

    def test_load_sqlite_missing_file(self, mock_feature):
        Foo = attr.make_class('Foo', ['c1', 'c2'])
        with pytest.raises(FileNotFoundError):
            list(mock_feature.load_sqlite(
                'nonexistent.sqlite',
                table='t1',
                cls=Foo,
            ))

    def test_load_mozlz4(self, mock_feature):
        assert mock_feature.load_mozlz4('test_mozlz4.lz4') == b'foo'
        with pytest.raises(NotMozLz4Error):
            mock_feature.load_mozlz4('test_json.json')

    def test_load_json_mozlz4(self, mock_feature):
        data = mock_feature.load_json_mozlz4('addonStartup.json.lz4')
        assert 'app-system-defaults' in data

    def test_write_json_mozlz4(self, mock_feature):
        mock_feature.write_json_mozlz4('test_json.json.lz4', {'foo': 'bar'})
        data = mock_feature.load_json_mozlz4('test_json.json.lz4')
        assert data == {'foo': 'bar'}


class TestSmallFeatures:

    def test_downloads(self, mock_session, capsys):
        Downloads(mock_session)()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert any(l.endswith(' file:///foo/bar') for l in lines)
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

    def test_table(self, mock_session, capsys):
        Permissions(mock_session, format='table')()
        out, _ = capsys.readouterr()
        assert ['https://two.example/',
                'permission2'] in (line.split() for line in out.split('\n'))

    def test_csv(self, mock_session, capsys):
        Permissions(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert len(data) == 4
        assert data[0] == ['host', 'permission']
        assert ['https://two.example/', 'permission2'] in data

    def test_summary(self, mock_session, capsys):
        Permissions(mock_session, summary=True)()
        out, _ = capsys.readouterr()
        assert '3 permissions found' in out


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

    def test_list(self, mock_session, capsys):
        Visits(mock_session, format='list')()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert '%s %s' % (datetime.fromtimestamp(1), 'http://one.example/') \
            in lines

    def test_csv(self, mock_session, capsys):
        Visits(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert data[0] == ['id', 'from_visit', 'visit_date', 'url']
        assert ['1', '2', '1', 'http://one.example/']


class TestCookiesFeature:

    def test_single_cookie(self):
        cookie = Cookie(name='foo', value='bar', host='x')
        assert str(cookie) == 'foo=bar; Domain=x'

        cookie = Cookie(name='foo', value='bar', host='one.example',
                        path='/baz', secure=True, http_only=True)
        assert all(x in str(cookie).lower() for x in ['foo=bar', 'path=/baz',
                   'secure', 'httponly', 'domain=one.example'])

    def test_list(self, mock_session, capsys):
        Cookies(mock_session, format='list')()
        out, _ = capsys.readouterr()
        assert any(line.startswith('k1=v1') for line in out.split('\n'))

        Cookies(mock_session, host='tw*.example', format='list')()
        out, _ = capsys.readouterr()
        assert out.startswith('k2=v2')

    def test_csv(self, mock_session, capsys):
        Cookies(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert ['k1', 'v1', 'one.example', '/', '1', '0'] in data

    def test_sessionstore(self, mock_session):
        file = session_file_type('sessionstore')
        assert file == session_file_type('sessionstore.jsonlz4')
        assert file != session_file_type('nonexistent')

        cookies = Cookies(mock_session).load_ss_cookies('sessionstore.jsonlz4')
        assert any((c.name, c.value, c.host) == ('sk2', 'sv2', 'two.example')
                   for c in cookies)

    def test_sessionstore_missing_file(self, mock_session):
        with pytest.raises(FatalError, match='not found'):
            Cookies(mock_session, session_file='nonexistent', format='list')()


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

    def test_csv(self, mock_session, capsys):
        Addons(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert data[0] == ['id', 'name', 'version', 'enabled', 'signed',
                           'visible', 'type', 'path', 'location']
        assert ['foo@bar', 'fooextension', '1.2.3', 'True', 'preliminary',
                'True', 'type1', '/foo/bar', 'app-profile'] in data
        assert ['bar@baz', 'barextension', '0.1rc', 'False', '', 'False',
                'type2', '/bar/baz', 'app-profile'] in data

    def test_list(self, mock_session, capsys):
        Addons(mock_session, format='list')()
        out, _ = capsys.readouterr()
        assert out.startswith('fooextension')
        assert all(x in out for x in ['preliminary', 'disabled'])

    def test_short(self, mock_session, capsys):
        Addons(mock_session, format='short')()
        out, _ = capsys.readouterr()
        assert 'foo@bar \'fooextension\'' in out

    def test_addons_json(self, mock_session, capsys):
        Addons(mock_session, show_addons_json=True)()
        out, _ = capsys.readouterr()
        assert 'fooextension (foo@bar)' in out

    def test_addon_startup_json(self, mock_session, capsys):
        Addons(mock_session, show_startup_json=True)()
        out, _ = capsys.readouterr()
        assert '/foo/bar (enabled)' in out

    def test_summary(self, mock_session, capsys):
        Addons(mock_session, summary=True)()
        out, _ = capsys.readouterr()
        assert out == '3 addons found. (2 enabled)\n'


class TestLoginsFeature:

    def test_formats(self, mock_session, capsys):
        Logins(mock_session, password='master', format='table')()
        out, _ = capsys.readouterr()
        assert all(x in out for x in ['foo', 'bar'])

        Logins(mock_session, password='master', format='list')()
        out, _ = capsys.readouterr()
        assert all(x in out for x in ['foo', 'bar'])

        Logins(mock_session, password='master', format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert ['http://one.example', 'foo', 'bar'] in data

    def test_no_libnss(self, mock_session):
        with pytest.raises(FatalError, match='Can\'t open libnss'):
            Logins(mock_session, libnss='nonexistent', format='csv')()

    def test_pw_prompt(self, mock_session, capsys, monkeypatch):
        import getpass # noqa
        def mock_getpass(*args, **kwargs):
            return 'master'
        monkeypatch.setattr('getpass.getpass', mock_getpass)
        Logins(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        assert 'foo' in out

    def test_wrong_pw(self, mock_session, capsys):
        with pytest.raises(FatalError, match='SEC_ERROR_BAD_PASSWORD'):
            Logins(mock_session, password='wrong', format='csv')()


class TestPreferencesFeature:

    def test_preferences(self, mock_session, capsys):
        Preferences(mock_session)()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert 'foo.bar = false' in lines
        assert 'baz = 456' in lines
        assert 'abc = "def"' in lines
        assert 'userkey = "userval"' in lines

    def test_summary(self, mock_session, capsys):
        Preferences(mock_session, summary=True)()
        out, _ = capsys.readouterr()
        assert out == '6 custom preferences found.\n'

    def test_parse_prefs(self, mock_session):
        feature = Preferences(mock_session, summary=True)
        prefs = list(feature.parse_prefs())
        assert sorted(prefs) == sorted([
            Preference('foo.bar', False),
            Preference('baz', 456),
            Preference('abc', 'def'),
            Preference('userkey', 'userval'),
            Preference("beacon.enabled", True),
            Preference("browser.search.region", "US"),
        ])

    @mark.web
    def test_recommended(self, mock_session, capsys):
        Preferences(mock_session, check_recommended=True)()
        out, _ = capsys.readouterr()
        assert 'Reason: Disable' in out
        assert 'Should: false' in nomarkup(out)
        assert 'Should: "US"' in nomarkup(out)

    def test_recommended_from_file(self, mock_session, capsys, tmpdir):
        userjs_recommended = dedent('''
        // PREF: foo
        // bar
        user_pref("userkey",		"other");

        // PREF: abc
        // def
        user_pref("pref2",		true);
        ''')
        path = tmpdir.join('recommended.js')
        path.write(userjs_recommended)
        Preferences(mock_session, check_recommended=True,
                    recommended_source=path)()
        out, _ = capsys.readouterr()
        assert 'Should: "other"' in nomarkup(out)
        assert '1 bad values found.' in out

        Preferences(mock_session, check_recommended=True,
                    recommended_source='/dev/null')()
        out, _ = capsys.readouterr()
        assert 'All preferences seem good.' in out

    def test_no_prefs(self, capsys, tmpdir):
        session = Session(profile=tmpdir)
        Preferences(session)()
        out, _ = capsys.readouterr()
        assert 'No preferences found.' in out


class TestInfectFeature:

    def test_check(self, mock_session, capsys):
        Infect(mock_session, want_check=True)()
        out, _ = capsys.readouterr()
        assert 'doesn\'t seem (fully) installed' in out

    def test_infect_cycle(self, mock_session, capsys, monkeypatch):
        def assert_not_installed():
            Infect(mock_session, want_check=True)()
            out, _ = capsys.readouterr()
            assert 'doesn\'t seem (fully) installed' in out

        def assert_installed():
            Infect(mock_session, want_check=True)()
            out, _ = capsys.readouterr()
            assert 'Extension seems installed' in out

        assert_not_installed()

        # Start infect, but cancel before execution
        monkeypatch.setattr('builtins.input', lambda: 'n')
        with pytest.raises(FatalError, match='Cancelled.'):
            Infect(mock_session)()

        # Start infect and confirm
        monkeypatch.setattr('builtins.input', lambda: 'y')
        Infect(mock_session)()
        out, err = capsys.readouterr()
        assert 'Installing' in out
        assert 'Warning:' not in err

        assert_installed()

        # Try to install again, which should raise warnings
        Infect(mock_session)()
        out, err = capsys.readouterr()
        assert 'Addon entry "infect@example.com" already exists.' in err
        assert 'Addon already registered in "addonStartup.json.lz4".' in err
        assert 'XPI already exists at' in err

        # Uninstall
        Infect(mock_session, want_uninstall=True)()
        out, err = capsys.readouterr()
        assert 'Updating "extensions.json".' in out
        assert 'Updating "addonStartup.json.lz4".' in out
        assert 'Warning:' not in err

        assert_not_installed()

        # Uninstall again, which should raise warnings
        Infect(mock_session, want_uninstall=True)()
        out, err = capsys.readouterr()
        assert 'Warning: ' in err
        assert 'Can\'t remove addon from "extensions.json".' in err
        assert 'Can\'t remove addon entry from "addonStartup.json.lz4"' in err
        assert 'Can\'t remove XPI.'

    @mark.unstable
    def test_infect_cycle_with_firefox(self, capsys, tmpdir, monkeypatch):
        # TODO Make this test work on Travis
        timeout = 10
        profile_dir = Path(tmpdir) / 'realprofile'

        def run_firefox():
            return subprocess.Popen(
                ['firefox', '--profile', str(profile_dir), '-headless']
            )

        os.makedirs(profile_dir)

        p = run_firefox()
        t_max = time.time() + timeout
        while True:
            # Assert that profile has been initialized
            if (profile_dir / 'times.json').exists() and \
               (profile_dir / 'addonStartup.json.lz4').exists():
                break
            if time.time() > t_max:
                raise Exception('Firefox timeout')
            time.sleep(0.01)
        p.terminate()

        # Remove file so we can observe when it's re-created
        os.remove(profile_dir / 'times.json')

        # Firefox needs to run a second time before we can install the addon
        p = run_firefox()
        t_max = time.time() + timeout
        while True:
            # Assert that profile has been initialized
            if (profile_dir / 'times.json').exists():
                break
            if time.time() > t_max:
                raise Exception('Firefox timeout')
            time.sleep(0.01)
        p.terminate()

        # Addon should not be installed
        session = Session(profile=profile_dir)
        Infect(session, want_check=True)()
        out, _ = capsys.readouterr()
        assert 'doesn\'t seem (fully) installed' in out

        # Install addon
        Infect(session, yes=True)()

        # Addon should be installed
        Infect(session, want_check=True)()
        out, _ = capsys.readouterr()
        assert 'Extension seems installed' in out

        # Wait for reverse shell and interact with it
        p = run_firefox()
        s = socket(AF_INET, SOCK_STREAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        s.settimeout(timeout)
        s.bind(('127.0.0.1', 8123))
        s.listen(1)
        conn, addr = s.accept()
        data = conn.recv(1024)
        assert b'OHAI' in data
        conn.send(b'window\n')
        data = conn.recv(1024)
        assert b'ChromeWindow' in data
        conn.close()

        p.terminate()


class TestSummaryFeature:

    def test_creation_date(self, mock_session):
        summary = Summary(mock_session)
        assert summary.creation_date() == datetime.fromtimestamp(1)

    def test_summary(self, mock_session, capsys):
        Summary(mock_session)()
        out, _ = capsys.readouterr()
        assert 'custom preferences found' in out
        # TODO make proper summary tests
