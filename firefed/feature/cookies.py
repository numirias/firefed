from collections import defaultdict
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
import sqlite3

from attr import attrib, attrs

from firefed.feature import Feature, arg, formatter
from firefed.output import out
from firefed.util import fatal


@attrs(hash=True)
class Cookie:

    name = attrib()
    value = attrib()
    host = attrib()
    path = attrib(default=None)
    expiry = attrib(default=None)
    secure = attrib(default=None, converter=bool)
    http_only = attrib(default=None, converter=bool)
    same_site = attrib(default=None, converter=bool)

    def __str__(self):
        # Re-assemble cookies based roughly on the 'Set-Cookie' format
        s = '%s=%s' % (self.name, self.value)
        if self.host:
            s += '; Domain=%s' % self.host
        if self.secure:
            s += '; Secure'
        if self.http_only:
            s += '; HttpOnly'
        if self.same_site:
            s += '; SameSite=%s' % ('lax' if self.same_site == 1 else 'strict')
        if self.expiry:
            try:
                date = datetime.fromtimestamp(self.expiry, tz=timezone.utc). \
                    strftime('%a, %d %b %Y %H:%M:%S %Z').replace('UTC', 'GMT')
            except ValueError:
                pass
            else:
                s += '; Expires=%s' % date
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
    'sameSite': 'same_site',
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
    """List cookies.

    Don't find a cookie you have definitely set? Not all cookies are
    immediately written to the cookie store. You possibly need to close the
    browser first to force all cookies being written to disk.
    """
    host = \
        arg('-H', '--host', help='filter by hostname (glob)')
    want_all_sources = \
        arg('-a', '--all', action='store_true', help='show cookies from all '
            'sources, including all available session files')
    session_file = \
        arg('-S', '--session-file', type=session_file_type, help='extract '
            'cookies from session file (you can use %s as shortcuts for '
            'default file locations)' % ', '.join('"%s"' % s for s in
                                                  session_file_map))

    def prepare(self):
        cookies = set()
        if self.want_all_sources:
            for source in session_file_map.values():
                try:
                    cookies |= set(self.load_ss_cookies(source))
                except FileNotFoundError:
                    pass
        elif self.session_file:
            try:
                cookies |= set(self.load_ss_cookies(self.session_file))
            except FileNotFoundError as e:
                fatal('Session file "%s" not found.' % e.filename)
        if not self.session_file:
            try:
                db_cookies = self.load_sqlite_cookies(column_map)
            except sqlite3.OperationalError as e:
                if str(e) == 'no such column: sameSite':
                    new_map = column_map.copy()
                    del new_map['sameSite']
                    # XXX This is a bit of a hack to handle a missing sameSite
                    # column. Should be cleaned up.
                    new_map['null'] = 'same_site'
                    db_cookies = self.load_sqlite_cookies(new_map)
                else:
                    raise
            cookies |= set(db_cookies)
        if self.host:
            cookies = [c for c in cookies if fnmatch(c.host, self.host)]
        self.cookies = list(cookies)

    def load_sqlite_cookies(self, column_map):
        return self.load_sqlite(
            db='cookies.sqlite',
            table='moz_cookies',
            cls=Cookie,
            column_map=column_map
        )

    def load_ss_cookies(self, path):
        data = self.load_json_mozlz4(path)
        cookies = data['cookies']
        return [Cookie(
            host=cookie.get('host', ''),
            name=cookie.get('name', ''),
            value=cookie.get('value', ''),
            path=cookie.get('path', None),
            secure=cookie.get('secure', False),
            http_only=cookie.get('httponly', False),
        ) for cookie in cookies]

    def run(self):
        self.build_format()

    def summarize(self):
        out('%d cookies found.' % len(list(self.cookies)))

    @formatter('setcookie', default=True)
    def format_setcookie(self):
        for cookie in self.cookies:
            out(cookie)

    @formatter('list')
    def format_list(self):
        host_map = defaultdict(list)
        for cookie in self.cookies:
            host_map[cookie.host].append(cookie)
        for host, cookies in host_map.items():
            out(host)
            for cookie in cookies:
                out('    %s = %s' % (cookie.name, cookie.value))
            out()

    @formatter('csv')
    def format_csv(self):
        Feature.csv_from_items(self.cookies)
