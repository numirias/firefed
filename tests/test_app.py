import pytest
from unittest import mock
import sys

import firefed.__main__
from firefed import Session


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


