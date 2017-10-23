from feature import Feature, SqliteTableFeature
from output import info


class Forms(SqliteTableFeature, Feature):

    db_file = 'formhistory.sqlite'
    table_name = 'moz_formhistory'
    num_text = '%s form field entries found.'
    fields = ['fieldname', 'value']

    def process_result(self, result):
        for field, val in result:
            info('%s=%s' % (field, val))
