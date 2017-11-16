import pytest
from unittest import mock
import sys
import csv
from io import StringIO

import firefed.__main__
from firefed import Session


def parse_csv(str_):
    return list(csv.reader(StringIO(str_)))

@pytest.fixture(scope='function')
def feature(mock_profile, parser):
    def func(*more_args):
        args = parser.parse_args(['--profile', str(mock_profile), *more_args])
        Session(args)
    return func


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

    # def test_main_with_feature(self, mock_profile):
    #     argv = ['firefed', '--profile', str(mock_profile), 'summary']
    #     with mock.patch.object(sys, 'argv', argv):
    #         firefed.__main__.main()


# class TestFeatures:

#     def test_permissions(self, feature, capsys):
#         feature('permissions', '--format', 'table')
#         out, _ = capsys.readouterr()
#         assert ['https://two.example/', 'permission2'] in (line.split() for line in out.split('\n'))
#         feature('permissions', '--format', 'csv')
#         out, _ = capsys.readouterr()
#         data = parse_csv(out)
#         assert len(data) == 4
#         assert data[0] == ['host', 'permission']
#         assert ['https://two.example/', 'permission2'] in data
