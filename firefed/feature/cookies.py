from fnmatch import fnmatch
import json
from pathlib import Path

from attr import attrib, attrs

from firefed.feature import Feature, arg, formatter
from firefed.output import fatal, out


@attrs
class Cookie:

    name = attrib()
    value = attrib()
    host = attrib()
    path = attrib(default=None)
    secure = attrib(default=None)
    http_only = attrib(default=None)

    def __str__(self):
        # Re-assemble cookies based roughly on the 'Set-Cookie' format
        s = '%s=%s' % (self.name, self.value)
        if self.host:
            s += '; Domain=%s' % self.host
        if self.secure:
            s += '; Secure'
        if self.http_only:
            s += '; HttpOnly'
        if self.path and self.path != '/':
            s += '; Path=%s' % self.path
        return s

column_map = {
    'name': 'name',
    'value': 'value',
    'host': 'host',
    'path': 'path',
    'isSecure': 'secure',
    'isHttpOnly': 'http_only',
}

session_file_map = {
    'recovery': Path('sessionstore-backups/recovery.jsonlz4'),
    'previous': Path('sessionstore-backups/previous.jsonlz4'),
    'sessionstore': Path('sessionstore.jsonlz4'),
}

def session_file_type(key_or_path):
    try:
        return session_file_map[key_or_path]
    except KeyError:
        return Path(key_or_path)

@attrs
class Cookies(Feature):

    host = arg('-H', '--host', help='filter by hostname (glob)')
    session_file = arg('-S', '--session-file', type=session_file_type,
                       help='extract cookies from session file (you can use %s'
                       'as shortcuts for default file locations)' %
                       ', '.join('"%s"' % s for s in session_file_map))

    def prepare(self):
        if self.session_file:
            try:
                cookies = self.load_ss_cookies(self.session_file)
            except FileNotFoundError as e:
                fatal('Session file "%s" not found.' % e.filename)
        else:
            cookies = self.load_sqlite(
                db='cookies.sqlite',
                table='moz_cookies',
                cls=Cookie,
                column_map=column_map
            )
        if self.host:
            cookies = [c for c in cookies if fnmatch(c.host, self.host)]
        self.cookies = cookies

    def load_ss_cookies(self, path):
        data = json.loads(self.load_mozlz4(path))
        cookies = data['cookies']
        return [Cookie(
            host=cookie['host'],
            name=cookie['name'],
            value=cookie['value'],
            path=cookie.get('path', None),
            secure=cookie.get('secure', False),
            http_only=cookie.get('httponly', False),
        ) for cookie in cookies]

    def run(self):
        self.build_format()

    def summarize(self):
        out('%d cookies found.' % len(self.cookies))

    @formatter('list', default=True)
    def format_list(self):
        for cookie in self.cookies:
            out(cookie)

    @formatter('csv')
    def format_csv(self):
        Feature.csv_from_items(self.cookies)
