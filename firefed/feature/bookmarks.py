import csv
import sys
from collections import namedtuple

from firefed.feature import Feature, output_formats
from firefed.output import info, good
from firefed.util import moz_timestamp


DIRECTORY_TYPE = 2
Bookmark = namedtuple('Bookmark', 'id parent type title guid added '
                                  'last_modified url')


@output_formats(['tree', 'list', 'csv'], default='tree')
class Bookmarks(Feature):

    def run(self):
        res = self.exec_sqlite(
            'places.sqlite',
            '''SELECT b.id, b.parent, b.type, b.title, b.guid, b.dateAdded,
            b.lastModified, p.url FROM moz_bookmarks b LEFT JOIN moz_places p
            ON b.fk = p.id
            '''
        )
        bmarks = [Bookmark(*row) for row in res]
        # Remove pseudo-bookmarks from list
        bmarks = [b for b in bmarks if not str(b.url).startswith('place:')]
        self.build_format(bmarks)

    @staticmethod
    def build_tree(bookmarks):
        bookmark_map = {b.id: b for b in bookmarks}
        def walk(node, depth=0):
            if node.type == DIRECTORY_TYPE:
                text = good('[%s]') % node.title
                info('%s%s' % (depth * 4 * ' ', text))
            else:
                info('%s* %s' % (depth * 4 * ' ', node.title))
                info('%s%s' % ((depth + 1) * 4 * ' ', node.url))
            children = [n for n in bookmarks if n.parent == node.id]
            for child in children:
                walk(child, depth + 1)
        for bookmark in bookmarks:
            try:
                parent_guid = bookmark_map[bookmark.parent].guid
            except KeyError:
                continue
            if bookmark.title == '':
                continue
            if parent_guid != 'root________':
                continue
            walk(bookmark)

    @staticmethod
    def build_list(bookmarks):
        for bookmark in bookmarks:
            if not bookmark.url:
                continue
            info('%s\n    %s' % (bookmark.title, bookmark.url))

    @staticmethod
    def build_csv(bookmarks):
        writer = csv.writer(sys.stdout)
        writer.writerow(('title', 'url', 'added', 'last_modified'))
        for b in bookmarks:
            if not b.url:
                continue
            writer.writerow((b.title, b.url, moz_timestamp(b.added),
                             moz_timestamp(b.last_modified)))
