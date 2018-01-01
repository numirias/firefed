import attr
from attr import attrs

from firefed.feature import Feature, formatter, arg
from firefed.output import out


DOWNLOAD_TYPE = 10
DB = 'places.sqlite'


@attrs
class Downloads(Feature):

    def prepare(self):
        self.data = self.load_sqlite(
            db=DB,
            table='moz_annos',
            cls=attr.make_class('Download', ['anno_attribute_id', 'content']),
        )

    def summarize(self):
        out('%d downloads found.' % len(self.data))

    def run(self):
        for download in self.data:
            if download.anno_attribute_id != DOWNLOAD_TYPE:
                continue
            out('%s' % download.content)

@attrs
class Hosts(Feature):

    def prepare(self):
        self.data = self.load_sqlite(
            db=DB,
            table='moz_hosts',
            cls=attr.make_class('Host', ['host']),
        )

    def summarize(self):
        out('%d hosts found.' % len(self.data))

    def run(self):
        for host in self.data:
            out('%s' % host.host)

@attrs
class InputHistory(Feature):

    def prepare(self):
        self.data = self.load_sqlite(
            db=DB,
            table='moz_inputhistory',
            cls=attr.make_class('Input', ['input']),
        )

    def summarize(self):
        out('%d input history entries found.' % len(self.data))

    def run(self):
        for input in self.data:
            out('%s' % input.input)
