from feature import Feature, SqliteTableFeature
from output import info


class Cookies(SqliteTableFeature, Feature):

    db_file = 'cookies.sqlite'
    table_name = 'moz_cookies'
    num_text = '%s cookies found.'
    fields = ['name', 'value', 'baseDomain', 'host', 'path', 'isSecure', 'isHttpOnly']

    def process_result(self, result):
        for name, value, base, host, path, secure, http_only in result:
            # Re-assemble cookies based rougly on the 'Set-Cookie' format
            cookie = '%s: %s=%s' % (base, name, value)
            if base:
                cookie += '; Domain=%s' % host
            if secure:
                cookie += '; Secure'
            if http_only:
                cookie += '; HttpOnly'
            if path != '/':
                cookie += '; Path=%s' % path
            info(cookie)
