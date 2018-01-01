import csv
import sys
from collections import namedtuple
from datetime import datetime
import attr
from attr import attrs, attrib

from firefed.feature import Feature, arg, formatter
from firefed.util import moz_to_unix_timestamp
from firefed.output import out, csv_writer


@attrs
class Visit:

    id = attrib()
    from_visit = attrib()
    visit_date = attrib(converter=moz_to_unix_timestamp)
    url = attrib()

@attrs
class Visits(Feature):

    """Extract the history of visited URLs."""

    def prepare(self):
        visits = self.load_sqlite(
            db='places.sqlite',
            query='''SELECT v.id, v.from_visit, v.visit_date, p.url FROM
            moz_historyvisits v JOIN moz_places p ON v.place_id = p.id
            ''',
            cls=Visit,
        )
        visits.sort(key=lambda x: x.visit_date)
        self.visits = visits

    def summarize(self):
        out('%d visits found.' % len(self.visits))

    def run(self):
        self.build_format()

    @formatter('list', default=True)
    def list(self):
        for visit in self.visits:
            out(datetime.fromtimestamp(visit.visit_date), visit.url)

    @formatter('csv')
    def csv(self):
        Feature.csv_from_items(self.visits)
