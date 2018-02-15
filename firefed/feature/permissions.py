import attr
from attr import attrib, attrs

from firefed.feature import Feature, formatter
from firefed.output import out
from firefed.util import tabulate


@attrs
class Permissions(Feature):
    """List host permissions (e.g. location sharing).

    This feature extracts the stored permissions which the user has granted to
    particular hosts (e.g. popups, location sharing, desktop notifications).
    """

    perms = attrib(default=None, init=False)

    def prepare(self):
        self.perms = self.load_sqlite(
            db='permissions.sqlite',
            table='moz_perms',
            cls=attr.make_class('Permission', ['host', 'permission']),
            column_map={'origin': 'host', 'type': 'permission'},
        )

    def summarize(self):
        out('%d permissions found.' % len(list(self.perms)))

    def run(self):
        self.build_format()

    @formatter('table', default=True)
    def table(self):
        rows = [attr.astuple(p) for p in self.perms]
        tabulate(rows, headers=('Host', 'Permission'))

    @formatter('csv')
    def csv(self):
        Feature.csv_from_items(self.perms)
