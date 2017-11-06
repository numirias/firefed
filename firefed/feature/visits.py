from output import info
from datetime import datetime
import csv
import sys
import sqlite3
from collections import namedtuple

from feature import Feature, output_formats
from feature.util import moz_datetime, moz_timestamp


Visit = namedtuple('Visit', 'id from_visit visit_date url')


@output_formats(['list', 'csv'], default='list')
class Visits(Feature):

    def run(self):
        con = sqlite3.connect(self.profile_path('places.sqlite'))
        cursor = con.cursor()
        result = cursor.execute(
            'SELECT v.id, v.from_visit, v.visit_date, p.url FROM moz_historyvisits v JOIN moz_places p ON v.place_id = p.id'
        )
        visits = [Visit(*row) for row in result]
        visits.sort(key=lambda x: x.visit_date)
        self.build_format(visits)

    def build_list(self, visits):
        for visit in visits:
            info(moz_datetime(visit.visit_date), visit.url)

    def build_csv(self, visits):
        writer = csv.writer(sys.stdout)
        writer.writerow(Visit._fields)
        for visit in visits:
            writer.writerow((
                visit.id,
                visit.from_visit,
                moz_timestamp(visit.visit_date),
                visit.url,
            ))
