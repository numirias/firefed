import csv
import sys

from tabulate import tabulate
from feature import Feature, SqliteTableFeature
from output import info


class Permissions(SqliteTableFeature, Feature):

    db_file = 'permissions.sqlite'
    table_name = 'moz_perms'
    num_text = '%s site permissions found.'
    fields = ['origin', 'type']

    def add_arguments(parser):
        parser.add_argument(
            '-f',
            '--format',
            default='table',
            choices=['table', 'csv'],
            help='output format',
        )

    def process_result(self, result):
        if self.args.format == 'table':
            info(tabulate(result, headers=('Host', 'Permission')))
            return
        writer = csv.writer(sys.stdout)
        writer.writerow(('host', 'permission'))
        writer.writerows(result)

