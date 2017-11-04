from feature import Feature, SqliteTableFeature
from output import info
import csv
import sys
from datetime import datetime


class HistoryEntry:

    _fields = ['url', 'title', 'last_visit_date', 'visit_count']

    def __init__(self, **kwargs):
        for field in self._fields:
            setattr(self, field, kwargs[field])


class History(Feature):

    def add_arguments(parser):
        parser.add_argument(
            '-f',
            '--format',
            default='list',
            choices=['short', 'list', 'csv'],
            help='output format',
        )

    def run(self):
        entries = self.load_sqlite('places.sqlite', 'moz_places', HistoryEntry)
        # Filter out entries without last visit date (e.g. bookmarks)
        entries = [e for e in entries if e.last_visit_date is not None]
        entries.sort(key=lambda x: x.last_visit_date)
        getattr(self, 'build_%s' % self.args.format)(entries)

    def build_list(self, entries):
        for entry in entries:
            last_visit = datetime.fromtimestamp(entry.last_visit_date//1000000)
            info(entry.url)
            info('    Title:      %s' % entry.title)
            info('    Last visit: %s' % last_visit)
            info('    Visits:     %s' % entry.visit_count)
            info()

    def build_short(self, entries):
        for entry in entries:
            print(entry.url)

    def build_csv(self, entries):
        writer = csv.writer(sys.stdout)
        writer.writerow(HistoryEntry._fields)
        for entry in entries:
            writer.writerow((getattr(entry, key) for key in HistoryEntry._fields))


class Downloads(SqliteTableFeature, Feature):

    db_file = 'places.sqlite'
    table_name = 'moz_annos'
    num_text = '%s downloads found.'
    fields = ['anno_attribute_id', 'content']

    def process_result(self, result):
        for id, content in result:
            if id != 10:
                continue
            info('%s' % content)


class Bookmarks(SqliteTableFeature, Feature):

    db_file = 'places.sqlite'
    table_name = 'moz_bookmarks'
    num_text = '%s bookmarks found.'
    fields = ['type', 'title']

    def process_result(self, result):
        for type, title in result:
            if type == 2:
                continue
            info('%s' % title)


class Hosts(SqliteTableFeature, Feature):

    db_file = 'places.sqlite'
    table_name = 'moz_hosts'
    num_text = '%s hosts found.'
    fields = ['host']

    def process_result(self, result):
        for host in result:
            info('%s' % host)


class InputHistory(SqliteTableFeature, Feature):

    db_file = 'places.sqlite'
    table_name = 'moz_inputhistory'
    num_text = '%s search bar input entries found.'
    fields = ['input']

    def process_result(self, result):
        for input in result:
            info('%s' % input)
