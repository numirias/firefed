import argparse
from collections import namedtuple
from pathlib import Path
import pytest

from firefed import Session
from firefed.feature import Feature, output_formats, SqliteTableFeature
from firefed.feature.feature import NotMozLz4Exception


class TestFeature:

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

    def test_build_format(self, MockFeature, mock_session, capsys):
        res = None
        class MockFeatureFoo(MockFeature):
            def build_foo(self, arg):
                nonlocal res
                res = arg
        MockFeatureFoo(mock_session, format='foo').build_format(arg='baz')
        assert res == 'baz'

    def test_sqlite_table_feature(self, mock_session, capsys):
        res = None
        class SomeFeature(SqliteTableFeature, Feature):
            db_file = 'test_sqlite.sqlite'
            table_name = 't1'
            num_text = '%s rows'
            fields = ['c1', 'c2']
            def process_result(self, res_):
                nonlocal res
                res = res_
        feature = SomeFeature(mock_session)
        feature()
        assert ('r1v1', 'r1v2') in res
