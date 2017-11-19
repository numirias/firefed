import csv
from fnmatch import fnmatch
import json
import lz4
import os
from pathlib import Path
import sys

from firefed.feature import Feature, output_formats, argument
from firefed.output import info, error


class Cookie:

    _column_map = {
        'name': 'name',
        'value': 'value',
        'host': 'host',
        'path': 'path',
        'isSecure': 'secure',
        'isHttpOnly': 'http_only',
    }
    _fields = tuple(_column_map.values())

    def __init__(self, **kwargs):
        for field in self._fields:
            try:
                setattr(self, field, kwargs[field])
            except KeyError:
                setattr(self, field, None)

    def __str__(self):
        # Re-assemble cookies based rougly on the 'Set-Cookie' format
        text = '%s=%s' % (self.name, self.value)
        if self.host:
            text += '; Domain=%s' % self.host
        if self.secure:
            text += '; Secure'
        if self.http_only:
            text += '; HttpOnly'
        if self.path and self.path != '/':
            text += '; Path=%s' % self.path
        return text

session_file_map = {
    'recovery': Path('sessionstore-backups/recovery.jsonlz4'),
    'previous': Path('sessionstore-backups/previous.jsonlz4'),
    'sessionstore': Path('sessionstore.jsonlz4'),
}

def session_file(key):
    try:
        return session_file_map[key]
    except KeyError:
        return Path(key)


@output_formats(['list', 'csv'], default='list')
@argument('-H', '--host', help='filter by hostname (glob)')
@argument('-s', '--session-file', type=session_file, help='extract cookies \
          from session file (you can use %s as shortcuts for default file \
          locations)' % ', '.join('"%s"' % s for s in session_file_map))
class Cookies(Feature):

    def run(self):
        if self.session_file:
            try:
                cookies = self.load_ss_cookies(self.session_file)
            except FileNotFoundError as e:
                error('Session file "%s" not found.' % e.filename)
                return
        else:
            cookies = self.load_sqlite('cookies.sqlite', 'moz_cookies', Cookie)
        if self.host:
            cookies = [c for c in cookies if fnmatch(c.host, self.host)]
        self.build_format(cookies)

    def load_ss_cookies(self, path):
        data = json.loads(self.load_mozlz4(path))
        cookies = data['cookies']
        return [Cookie(
            host=cookie['host'],
            name=cookie['name'],
            value=cookie['value'],
            path=cookie['path'] if 'path' in cookie else None,
            secure=cookie['secure'] if 'secure' in cookie else False,
            http_only=cookie['httponly'] if 'httponly' in cookie else False,
        ) for cookie in cookies]

    def build_list(self, cookies):
        for cookie in cookies:
            print(cookie)

    def build_csv(self, cookies):
        writer = csv.writer(sys.stdout)
        writer.writerow(Cookie._fields)
        for cookie in cookies:
            writer.writerow((getattr(cookie, key) for key in Cookie._fields))
