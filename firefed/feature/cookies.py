import json
import lz4
import os
from fnmatch import fnmatch
import csv
import sys

from feature import Feature
from output import info, error


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
            setattr(self, field, kwargs[field])

    def __str__(self):
        # Re-assemble cookies based rougly on the 'Set-Cookie' format
        text = '%s=%s' % (self.name, self.value)
        if self.host:
            text += '; Domain=%s' % self.host
        if self.secure:
            text += '; Secure'
        if self.http_only:
            text += '; HttpOnly'
        if self.path != '/':
            text += '; Path=%s' % self.path
        return text


def session_file(key):
    session_file_map = {
        'recovery': os.path.join('sessionstore-backups', 'recovery.jsonlz4'),
        'previous': os.path.join('sessionstore-backups', 'previous.jsonlz4'),
        'sessionstore': 'sessionstore.jsonlz4',
    }
    try:
        return session_file_map[key]
    except KeyError:
        return key


class Cookies(Feature):

    def add_arguments(parser):
        parser.add_argument(
            '-f',
            '--format',
            default='list',
            choices=['list', 'csv'],
            help='output format',
        )
        parser.add_argument(
            '-H',
            '--host',
            help='glob for matching host name',
        )
        parser.add_argument(
            '-s',
            '--session-file',
            type=session_file,
            help='extract cookies from session file ("recovery", "previous", "sessionstore" are shortcuts for default file locations)',
        )

    def run(self):
        if self.args.session_file:
            try:
                cookies = self.load_ss_cookies(self.args.session_file)
            except FileNotFoundError as e:
                error('File "%s" not found.' % e.filename)
                return
        else:
            cookies = self.load_sqlite('cookies.sqlite', 'moz_cookies', Cookie)
        host_pattern = self.args.host
        if host_pattern:
            cookies = [c for c in cookies if fnmatch(c.host, host_pattern)]
        getattr(self, 'build_%s' % self.args.format)(cookies)

    def build_list(self, cookies):
        for cookie in cookies:
            print(cookie)

    def build_csv(self, cookies):
        writer = csv.writer(sys.stdout)
        writer.writerow(Cookie._fields)
        for cookie in cookies:
            writer.writerow((getattr(cookie, key) for key in Cookie._fields))

    def load_ss_cookies(self, path):
        data = json.loads(self.load_moz_lz4(path))
        cookies = data['cookies']
        return [Cookie(
            host=cookie['host'],
            name=cookie['name'],
            value=cookie['value'],
            path=cookie['path'],
            secure=cookie['secure'] if 'secure' in cookie else False,
            http_only=cookie['httponly'] if 'httponly' in cookie else False,
        ) for cookie in cookies]
