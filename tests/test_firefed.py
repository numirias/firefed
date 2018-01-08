import csv
from datetime import datetime
from io import StringIO
from pathlib import Path

import attr
from attr import attrs
import pytest

from firefed import Session
from firefed.feature import (Addons, Bookmarks, Cookies, Downloads, Feature,
                             Forms, History, Hosts, Infect, InputHistory,
                             Logins, Permissions, Preferences, Summary, Visits,
                             arg, formatter)
from firefed.feature.cookies import Cookie, session_file_type
from firefed.feature.feature import NotMozLz4Error


def parse_csv(str_):
    return list(csv.reader(StringIO(str_)))


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
        with pytest.raises(SystemExit) as e:
            list(mock_feature.load_sqlite(
                'nonexistent.sqlite',
                table='t1',
                cls=Foo,
            ))
        assert e.value.code == 1
        # TODO Catch custom exception here instead of SystemExit
        # TODO Dedicated test for profile_path(..., must_exist=True)

    def test_load_mozlz4(self, mock_feature):
        assert mock_feature.load_mozlz4('test_mozlz4.lz4') == b'foo'
        with pytest.raises(NotMozLz4Error):
            mock_feature.load_mozlz4('test_json.json')


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

    def test_sessionstore(self, mock_session, capsys):
        file = session_file_type('sessionstore')
        assert file == session_file_type('sessionstore.jsonlz4')
        assert file != session_file_type('nonexistent')

        with pytest.raises(SystemExit) as e:
            Cookies(mock_session, session_file='nonexistent', format='list')()
        assert e.value.code == 1
        _, err = capsys.readouterr()
        # TODO Instead of reading stderr, catch custom fatal error
        assert 'not exist' in err

        cookies = Cookies(mock_session).load_ss_cookies('sessionstore.jsonlz4')
        assert any((c.name, c.value, c.host) == ('sk2', 'sv2', 'two.example')
                   for c in cookies)


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
        assert data[0] == ['id', 'name', 'version', 'enabled', 'signed',
                           'visible']
        assert ['foo@bar', 'fooextension', '1.2.3', 'True', 'preliminary',
                'True'] in data
        assert ['bar@baz', 'barextension', '0.1rc', 'False', '', 'False'] \
            in data

        Addons(mock_session, format='list')()
        out, _ = capsys.readouterr()
        assert out.startswith('fooextension')
        assert all(x in out for x in ['preliminary', 'enabled'])

        Addons(mock_session, format='table')()
        out, _ = capsys.readouterr()
        assert 'fooextension' in out
        assert 'barextension' in out

    def test_summary(self, mock_session, capsys):
        Addons(mock_session, summary=True)()
        out, _ = capsys.readouterr()
        assert out == '3 addons found. (2 enabled)\n'

    def test_addons_by_id(self, mock_session, capsys):
        Addons(mock_session, format='csv', addon_id='foo@bar')()
        out, _ = capsys.readouterr()
        assert 'fooextension' in out
        assert 'barextension' not in out

    def test_addons_errors(self, mock_session):
        # Can't check outdated without version
        with pytest.raises(SystemExit) as e:
            Addons(mock_session, format='table', check_outdated=True)()
        assert e.value.code == 1

        # Can't check outdated if not list format
        with pytest.raises(SystemExit) as e:
            Addons(mock_session, format='list', check_outdated=True)()
        assert e.value.code == 1

    def test_addons_chcek_outdated(self, mock_session, monkeypatch):
        class Response:
            pass
        def get_bad_response(*args, **kwargs):
            res = Response()
            res.text = 'badxml'
            return res
        monkeypatch.setattr('requests.get', get_bad_response)
        with pytest.raises(SystemExit) as e:
            Addons(mock_session, format='list', check_outdated=True,
                   firefox_version='52')()
        assert e.value.code == 1
        # TODO Test good response


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

    def test_no_libnss(self, mock_session, capsys):
        with pytest.raises(SystemExit) as e:
            Logins(mock_session, libnss='nonexistent', format='csv')()
        _, err = capsys.readouterr()
        assert e.value.code == 1
        assert 'Can\'t open libnss' in err

    def test_pw_prompt(self, mock_session, capsys, monkeypatch):
        import getpass # noqa
        def mock_getpass(*args, **kwargs):
            return 'master'
        monkeypatch.setattr('getpass.getpass', mock_getpass)
        Logins(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        assert 'foo' in out

    def test_wrong_pw(self, mock_session, capsys):
        with pytest.raises(SystemExit) as e:
            Logins(mock_session, password='wrong', format='csv')()
        _, err = capsys.readouterr()
        assert e.value.code == 1
        assert 'Incorrect master password' in err


class TestPreferencesFeature:

    def test_preferences(self, mock_session, capsys):
        Preferences(mock_session)()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert 'foo.bar = false' in lines
        assert 'baz = 123' in lines
        assert 'abc = "def"' in lines
        # TODO More feature tests

    def test_summary(self, mock_session, capsys):
        Preferences(mock_session, summary=True)()
        out, _ = capsys.readouterr()
        assert out == '3 custom preferences found.\n'


class TestInfectFeature:

    def test_check(self, mock_session, capsys):
        Infect(mock_session, want_check=True)()
        out, _ = capsys.readouterr()
        assert 'doesn\'t seem fully installed' in out
        # TODO More feature tests


class TestSummaryFeature:

    def test_creation_date(self, mock_session):
        summary = Summary(mock_session)
        assert summary.creation_date() == datetime.fromtimestamp(1)

    def test_summary(self, mock_session, capsys):
        Summary(mock_session)()
        out, _ = capsys.readouterr()
        assert 'custom preferences found' in out
        # TODO make proper summary tests
