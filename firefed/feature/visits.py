import csv
import sys
from collections import namedtuple

from firefed.feature import Feature, output_formats
from firefed.util import moz_datetime, moz_timestamp
from firefed.output import info


Visit = namedtuple('Visit', 'id from_visit visit_date url')


@output_formats(['list', 'csv'], default='list')
class Visits(Feature):

    def run(self):
        res = self.exec_sqlite(
            'places.sqlite',
            '''SELECT v.id, v.from_visit, v.visit_date, p.url FROM
            moz_historyvisits v JOIN moz_places p ON v.place_id = p.id
            '''
        )
        visits = [Visit(*row) for row in res]
        visits.sort(key=lambda x: x.visit_date)
        self.build_format(visits)

    @staticmethod
    def build_list(visits):
        for visit in visits:
            info(moz_datetime(visit.visit_date), visit.url)

    @staticmethod
    def build_csv(visits):
        writer = csv.writer(sys.stdout)
        writer.writerow(Visit._fields)
        for visit in visits:
            writer.writerow((
                visit.id,
                visit.from_visit,
                moz_timestamp(visit.visit_date),
                visit.url,
            ))
