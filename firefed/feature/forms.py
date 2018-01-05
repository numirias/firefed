import attr
from attr import attrs

from firefed.feature import Feature
from firefed.output import out


@attrs
class Forms(Feature):
    """List form input history (search terms, address fields, etc.)."""

    def prepare(self):
        self.entries = self.load_sqlite(
            db='formhistory.sqlite',
            table='moz_formhistory',
            cls=attr.make_class('FormEntry', ['fieldname', 'value']),
        )

    def summarize(self):
        out('%d form entries found.' % len(self.entries))

    def run(self):
        for entry in self.entries:
            out('%s=%s' % (entry.fieldname, entry.value))
