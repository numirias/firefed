from firefed.feature import Feature, SqliteTableFeature
from firefed.output import info


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
