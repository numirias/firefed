from feature import Feature, SqliteTableFeature
from tabulate import tabulate
from output import info


class Permissions(SqliteTableFeature, Feature):

    db_file = 'permissions.sqlite'
    table_name = 'moz_perms'
    num_text = '%s site permissions found.'
    fields = ['origin', 'type']

    def process_result(self, result):
        info(tabulate(result, headers=('Host', 'Permission')))
