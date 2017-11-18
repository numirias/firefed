import argparse
from collections import namedtuple
import csv
from datetime import datetime
from io import StringIO
from pathlib import Path
import pytest

from firefed import Session
from firefed.feature import Feature, output_formats, sqlite_data, argument, Permissions, Forms, Bookmarks, History, Downloads, Hosts, InputHistory, Visits
from firefed.feature.feature import NotMozLz4Exception


def parse_csv(str_):
    return list(csv.reader(StringIO(str_)))


class TestFeature:

    def test_argument(self):
        @argument('-f', '--foo')
        class SomeFeature(Feature):
            def run(self):
                pass
        parser = argparse.ArgumentParser()
        SomeFeature.add_arguments(parser)
        assert parser.parse_args(['--foo', 'x']).foo == 'x'

    def test_output_formats(self):
        @output_formats(['a', 'b', 'c'], default='b')
        class SomeFeature(Feature):
            def run(self):
                pass
        parser = argparse.ArgumentParser()
        SomeFeature.add_arguments(parser)
        assert parser.parse_args([]).format == 'b'
        assert parser.parse_args(['--format', 'c']).format == 'c'

    def test_init(self, MockFeature, mock_session):
        feature = MockFeature(mock_session, arg1=2)
        assert feature.arg1 == 2

    def test_run(self, mock_session):
        has_run = False
        class MockFeature(Feature):
            def run(self):
                nonlocal has_run
                has_run = True
        MockFeature(mock_session)()
        assert has_run

    def test_profile_path(self, MockFeature):
        session = Session(profile='/foo/bar')
        feature = MockFeature(session)
        assert feature.profile_path('baz') == Path('/foo/bar/baz')

    def test_loading(self, mock_feature):
        assert mock_feature.load_json('test_json.json')['foo']['bar'] == 2

        Foo = namedtuple('Foo', 'c1 c2')
        foos = mock_feature.load_sqlite('test_sqlite.sqlite', 't1', Foo)
        assert Foo(c1='r1v1', c2='r1v2') in foos

        assert mock_feature.load_moz_lz4('test_moz_lz4.lz4') == b'foo'
        with pytest.raises(NotMozLz4Exception):
            mock_feature.load_moz_lz4('test_json.json')

    def test_exec_sqlite(self, mock_feature):
        res = mock_feature.exec_sqlite('test_sqlite.sqlite', 'SELECT c2 from t1')
        assert ('r2v2',) in res

    def test_build_format(self, MockFeature, mock_session):
        res = None
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


class TestFeatures:

    def test_permissions(self, mock_session, capsys):
        Permissions(mock_session, format='table')()
        out, _ = capsys.readouterr()
        assert ['https://two.example/', 'permission2'] in (line.split() for line in out.split('\n'))
        Permissions(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert len(data) == 4
        assert data[0] == ['host', 'permission']
        assert ['https://two.example/', 'permission2'] in data

    def test_forms(self, mock_session, capsys):
        Forms(mock_session)()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert 'ccc=ddd' in lines

    def test_history(self, mock_session, capsys):
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

    def test_visits(self, mock_session, capsys):
        Visits(mock_session, format='list')()
        out, _ = capsys.readouterr()
        lines = out.split('\n')
        assert '%s %s' % (datetime.fromtimestamp(1), 'http://one.example/') in lines

        Visits(mock_session, format='csv')()
        out, _ = capsys.readouterr()
        data = parse_csv(out)
        assert data[0] == ['id', 'from_visit', 'visit_date', 'url']
        assert ['1', '2', '1', 'http://one.example/']
