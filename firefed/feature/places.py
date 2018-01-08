from datetime import datetime

import attr
from attr import attrs, attrib

from firefed.feature import Feature
from firefed.output import out
from firefed.util import moz_to_unix_timestamp


DOWNLOAD_TYPE = 10
DB = 'places.sqlite'


@attrs
class Download:

    filename = attrib()
    date = attrib(converter=moz_to_unix_timestamp)
    anno_attribute_id = attrib()


@attrs
class Downloads(Feature):
    """List downloaded files."""

    def prepare(self):
        self.data = self.load_sqlite(
            db=DB,
            table='moz_annos',
            cls=Download,
            column_map={'dateAdded': 'date', 'content': 'filename'}
        )

    def summarize(self):
        out('%d downloads found.' % len(list(self.data)))

    def run(self):
        for download in self.data:
            if download.anno_attribute_id != DOWNLOAD_TYPE:
                continue
            out('%s %s' % (datetime.fromtimestamp(download.date),
                           download.filename))


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
