import csv
import sys
from tabulate import tabulate

from firefed.feature import Feature, output_formats, sqlite_data
from firefed.output import out


@output_formats(['table', 'csv'], default='table')
class Permissions(Feature):

    @sqlite_data(db='permissions.sqlite', table='moz_perms',
                 columns=['origin', 'type'])
    def run(self, data):
        if self.format == 'table':
            out(tabulate(data, headers=('Host', 'Permission')))
            return
        writer = csv.writer(sys.stdout)
        writer.writerow(('host', 'permission'))
        writer.writerows(data)
