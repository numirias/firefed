from datetime import datetime

from attr import attrib, attrs

from firefed.feature import Feature, formatter
from firefed.output import out, outitem
from firefed.util import moz_to_unix_timestamp


@attrs
class HistoryEntry:

    url = attrib()
    title = attrib()
    last_visit_date = attrib(converter=moz_to_unix_timestamp)
    visit_count = attrib()


@attrs
class History(Feature):
    """List history."""

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
            outitem(entry.url, [
                ('Title', entry.title),
                ('Last visit', last_visit),
                ('Visits', entry.visit_count),
            ])

    @formatter('short')
    def format_short(self):
        for entry in self.entries:
            out(entry.url)

    @formatter('csv')
    def format_csv(self):
        Feature.csv_from_items(self.entries)
