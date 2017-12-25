import csv
import sys

from firefed.feature import Feature, output_formats
from firefed.output import out
from firefed.util import moz_datetime, moz_timestamp


class HistoryEntry:  # TODO: Refactor as namedtuple?

    _fields = ['url', 'title', 'last_visit_date', 'visit_count']

    def __init__(self, **kwargs):
        for field in self._fields:
            setattr(self, field, kwargs[field])


@output_formats(['short', 'list', 'csv'], default='list')
class History(Feature):

    def run(self):
        entries = self.load_sqlite('places.sqlite', 'moz_places', HistoryEntry)
        # Filter out entries without last visit date (e.g. bookmarks)
        entries = [e for e in entries if e.last_visit_date is not None]
        entries.sort(key=lambda x: x.last_visit_date)
        self.build_format(entries)

    @staticmethod
    def build_list(entries):
        for entry in entries:
            last_visit = moz_datetime(entry.last_visit_date)
            out(entry.url)
            out('    Title:      %s' % entry.title)
            out('    Last visit: %s' % last_visit)
            out('    Visits:     %s' % entry.visit_count)
            out()

    @staticmethod
    def build_short(entries):
        for entry in entries:
            out(entry.url)

    @staticmethod
    def build_csv(entries):
        writer = csv.writer(sys.stdout)
        writer.writerow(HistoryEntry._fields)
        for entry in entries:
            writer.writerow((
                entry.url,
                entry.title,
                moz_timestamp(entry.last_visit_date),
                entry.visit_count,
            ))
