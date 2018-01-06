import attr
from attr import attrs

from firefed.feature import Feature
from firefed.output import out


DOWNLOAD_TYPE = 10
DB = 'places.sqlite'


@attrs
class Downloads(Feature):
    """List downloaded files."""

    def prepare(self):
        self.data = self.load_sqlite(
            db=DB,
            table='moz_annos',
            cls=attr.make_class('Download', ['anno_attribute_id', 'content']),
        )

    def summarize(self):
        out('%d downloads found.' % len(list(self.data)))

    def run(self):
        for download in self.data:
            if download.anno_attribute_id != DOWNLOAD_TYPE:
                continue
            out('%s' % download.content)


@attrs
class Hosts(Feature):
    """List known hosts."""

    def prepare(self):
        self.data = self.load_sqlite(
            db=DB,
            table='moz_hosts',
            cls=attr.make_class('Host', ['host']),
        )

    def summarize(self):
        out('%d hosts found.' % len(list(self.data)))

    def run(self):
        for host in self.data:
            out('%s' % host.host)


@attrs
class InputHistory(Feature):
    """List history of urlbar inputs (typed URLs)."""

    def prepare(self):
        self.data = self.load_sqlite(
            db=DB,
            table='moz_inputhistory',
            cls=attr.make_class('Input', ['input']),
        )

    def summarize(self):
        out('%d input history entries found.' % len(list(self.data)))

    def run(self):
        for entry in self.data:
            out('%s' % entry.input)
