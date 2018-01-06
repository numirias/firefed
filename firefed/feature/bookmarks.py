from attr import attrib, attrs

from firefed.feature import Feature, formatter
from firefed.output import csv_writer, good, out
from firefed.util import moz_to_unix_timestamp


DIRECTORY_TYPE = 2


@attrs
class Bookmark:

    id = attrib()
    parent = attrib()
    type = attrib()
    title = attrib()
    guid = attrib()
    added = attrib(converter=moz_to_unix_timestamp)
    last_modified = attrib(converter=moz_to_unix_timestamp)
    url = attrib()


@attrs
class Bookmarks(Feature):
    """List bookmarks."""

    def prepare(self):
        bmarks = self.load_sqlite(
            db='places.sqlite',
            query='''SELECT b.id, b.parent, b.type, b.title, b.guid, b.dateAdded,
            b.lastModified, p.url FROM moz_bookmarks b LEFT JOIN moz_places p
            ON b.fk = p.id
            ''',
            cls=Bookmark,
            column_map={
                'lastModified': 'last_modified',
                'dateAdded': 'added'
            },
        )
        # Remove pseudo-bookmarks from list
        bmarks = (b for b in bmarks if not str(b.url).startswith('place:'))
        self.bmarks = bmarks

    def summarize(self):
        out('%d bookmarks found.' % len(list(self.bmarks)))

    def run(self):
        self.build_format()

    @formatter('tree', default=True)
    def tree(self):
        bmarks = list(self.bmarks)
        bmark_map = {b.id: b for b in bmarks}
        def walk(node, depth=0):
            if node.type == DIRECTORY_TYPE:
                text = good('[%s]') % node.title
                out('%s%s' % (depth * 4 * ' ', text))
            else:
                out('%s* %s' % (depth * 4 * ' ', node.title))
                out('%s%s' % ((depth + 1) * 4 * ' ', node.url))
            children = [n for n in bmarks if n.parent == node.id]
            for child in children:
                walk(child, depth + 1)
        for bmark in bmarks:
            try:
                parent_guid = bmark_map[bmark.parent].guid
            except KeyError:
                continue
            if bmark.title == '':
                continue
            if parent_guid != 'root________':
                continue
            walk(bmark)

    @formatter('list')
    def list(self):
        for bmark in self.bmarks:
            if not bmark.url:
                continue
            out('%s\n    %s' % (bmark.title, bmark.url))

    @formatter('csv')
    def csv(self):
        writer = csv_writer()
        writer.writerow(('title', 'url', 'added', 'last_modified'))
        for b in self.bmarks:
            if not b.url:
                continue
            writer.writerow((b.title, b.url, b.added,
                             b.last_modified))
