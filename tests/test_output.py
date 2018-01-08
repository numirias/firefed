from firefed import Session, output


class TestOutput:

    def test_error(self, capsys):
        output.out('foo')
        out, err = capsys.readouterr()
        assert out == 'foo\n'
        assert err == ''
        output.error('foo')
        out, err = capsys.readouterr()
        assert out == ''
        assert 'foo' in err

    def test_logging(self, caplog, mock_profile):
        # TODO Globals are evil
        Session(profile=mock_profile, verbosity=0)
        assert caplog.text == ''
        Session(profile=mock_profile, verbosity=1)
        output.info('foo')
        assert 'foo' in caplog.text
