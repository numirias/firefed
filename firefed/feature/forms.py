from firefed.feature import Feature, sqlite_data
from firefed.output import out


class Forms(Feature):

    @sqlite_data(db='formhistory.sqlite', table='moz_formhistory',
                 columns=['fieldname', 'value'])
    def run(self, data):
        for field, val in data:
            out('%s=%s' % (field, val))
