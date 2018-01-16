from firefed import Session, output


class TestOutput:

    def test_error(self, stdouterr):
        output.out('foo')
        out, err = stdouterr()
        assert out == 'foo\n'
        assert err == ''
        output.error('foo')
        out, err = stdouterr()
        assert out == ''
        assert 'foo' in err

    def test_colors(self):
        assert 'x' in output.good('x')
        assert 'x' in output.bad('x')
        assert 'x' in output.okay('x')
        assert 'x' in output.disabled('x')

    def test_logging(self, caplog, mock_profile):
        session = Session(profile=mock_profile, verbosity=0)
        session.logger.info('foo')
        assert caplog.text == ''
        session = Session(profile=mock_profile, verbosity=1)
        session.logger.info('foo')
        assert 'foo' in caplog.text
