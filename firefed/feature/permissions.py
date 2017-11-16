import csv
import sys
from tabulate import tabulate

from firefed.feature import Feature, SqliteTableFeature, output_formats
from firefed.output import info


@output_formats(['table', 'csv'], default='table')
class Permissions(SqliteTableFeature, Feature):

    db_file = 'permissions.sqlite'
    table_name = 'moz_perms'
    num_text = '%s site permissions found.'
    fields = ['origin', 'type']

    def process_result(self, result):
        if self.format == 'table':
            info(tabulate(result, headers=('Host', 'Permission')))
            return
        writer = csv.writer(sys.stdout)
        writer.writerow(('host', 'permission'))
        writer.writerows(result)
