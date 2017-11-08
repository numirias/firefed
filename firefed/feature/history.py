import csv
import sys

from firefed.feature import Feature, output_formats
from firefed.feature.util import moz_datetime, moz_timestamp
from firefed.output import info


class HistoryEntry:

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

    def build_list(self, entries):
        for entry in entries:
            last_visit = moz_datetime(entry.last_visit_date)
            info(entry.url)
            info('    Title:      %s' % entry.title)
            info('    Last visit: %s' % last_visit)
            info('    Visits:     %s' % entry.visit_count)
            info()

    def build_short(self, entries):
        for entry in entries:
            info(entry.url)

    def build_csv(self, entries):
        writer = csv.writer(sys.stdout)
        writer.writerow(HistoryEntry._fields)
        for entry in entries:
            writer.writerow((
                entry.url,
                entry.title,
                moz_timestamp(entry.last_visit_date),
                entry.visit_count,
            ))
