import os
import re
import sys
from unittest import mock

import pytest

from firefed.util import FatalError
import firefed.__main__


def nomarkup(s):
    return re.sub(r'\x1b\[\d*m', '', s)


class TestMain:

    def test_main(self):
        with pytest.raises(SystemExit) as e:
            firefed.__main__.main()
        assert e.value.code == 2

    def test_run_on_bad_profile(self):
        argv = ['firefed', '--profile', '/dev/null', 'summary']
        with mock.patch.object(sys, 'argv', argv):
            with pytest.raises(FatalError, match='doesn\'t look like'):
                firefed.__main__.run()

    def test_exit_with_fatal_error(self, stdouterr, match):
        argv = ['firefed', '--profile', '/dev/null', 'summary']
        with pytest.raises(SystemExit) as e:
            with mock.patch.object(sys, 'argv', argv):
                firefed.__main__.main()
        assert e.value.code != 0
        out, err = stdouterr()
        assert out == ''
        assert match('.*Error:.*', err)

    def test_main_help(self, stdout):
        with mock.patch.object(sys, 'argv', ['firefed', '-h']):
            with pytest.raises(SystemExit) as e:
                firefed.__main__.main()
        assert e.value.code == 0
        assert stdout().startswith('usage:')

    def test_main_with_feature(self, mock_profile, stdout):
        argv = ['firefed', '--profile', str(mock_profile), 'summary']
        with mock.patch.object(sys, 'argv', argv):
            firefed.__main__.main()
        assert 'Profile created' in stdout()

    def test_show_profiles(self, stdout, monkeypatch, mock_home):
        monkeypatch.setitem(os.environ, 'HOME', str(mock_home))
        with mock.patch.object(sys, 'argv', ['firefed', '--profiles']):
            firefed.__main__.main()
        assert 'default [default]' in nomarkup(stdout())
