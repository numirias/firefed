from feature import Feature, SqliteTableFeature
from output import info


class History(SqliteTableFeature, Feature):

    db_file = 'places.sqlite'
    table_name = 'moz_places'
    num_text = '%s history entries found.'
    fields = ['url']

    def process_result(self, result):
        for url in result:
            info('%s' % url)


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
