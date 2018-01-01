import sys
import attr
from attr import attrs, attrib
from tabulate import tabulate

from firefed.feature import Feature, formatter, arg
from firefed.output import out, csv_writer


@attrs
class Permissions(Feature):
    """Extract permissions granted to particular hosts (e.g. location sharing).

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
        out('%d permissions found.' % len(self.perms))

    def run(self):
        self.build_format()

    @formatter('table', default=True)
    def table(self):
        rows = [attr.astuple(p) for p in self.perms]
        out(tabulate(rows, headers=('Host', 'Permission')))

    @formatter('csv')
    def csv(self):
        Feature.csv_from_items(self.perms)
