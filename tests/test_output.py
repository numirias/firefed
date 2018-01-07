from firefed import output


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
