from firefed.feature import Feature, sqlite_data
from firefed.output import info


DOWNLOAD_TYPE = 10


class Downloads(Feature):

    @sqlite_data(db='places.sqlite', table='moz_annos',
                 columns=['anno_attribute_id', 'content'])
    def run(self, data):
        for id_, content in data:
            if id_ != DOWNLOAD_TYPE:
                continue
            info('%s' % content)


class Hosts(Feature):

    @sqlite_data(db='places.sqlite', table='moz_hosts', columns=['host'])
    def run(self, data):
        for host in data:
            info('%s' % host)


class InputHistory(Feature):

    @sqlite_data(db='places.sqlite', table='moz_inputhistory',
                 columns=['input'])
    def run(self, data):
        for input_ in data:
            info('%s' % input_)
