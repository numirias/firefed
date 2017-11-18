from firefed.feature import Feature, sqlite_data
from firefed.output import info


class Forms(Feature):

    @sqlite_data(db='formhistory.sqlite', table='moz_formhistory', columns=['fieldname', 'value'])
    def run(self, data):
        for field, val in data:
            info('%s=%s' % (field, val))
