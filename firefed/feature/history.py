import sys
from datetime import datetime
import attr
from attr import attrs, attrib

from firefed.feature import Feature, formatter
from firefed.output import out, csv_writer
from firefed.util import moz_to_unix_timestamp, moz_datetime


@attrs
class HistoryEntry:

    url = attrib()
    title = attrib()
    last_visit_date = attrib(converter=moz_to_unix_timestamp)
    visit_count = attrib()


@attrs
class History(Feature):

    entries = attrib(default=None, init=False)

    def prepare(self):
        entries = self.load_sqlite(
            db='places.sqlite',
            table='moz_places',
            cls=HistoryEntry,
        )
        # Entries without last visit date can be dropped (e.g. bookmarks)
        entries = [e for e in entries if e.last_visit_date is not None]
        entries.sort(key=lambda x: x.last_visit_date)
        self.entries = entries

    def summarize(self):
        out('%d history entries found.' % len(self.entries))

    def run(self):
        self.build_format()

    @formatter('list', default=True)
    def list(self):
        for entry in self.entries:
            last_visit = datetime.fromtimestamp(entry.last_visit_date)
            out(entry.url)
            out('    Title:      %s' % entry.title)
            out('    Last visit: %s' % last_visit)
            out('    Visits:     %s' % entry.visit_count)
            out()

    @formatter('short')
    def format_short(self):
        for entry in self.entries:
            out(entry.url)

    @formatter('csv')
    def format_csv(self):
        Feature.csv_from_items(self.entries)
