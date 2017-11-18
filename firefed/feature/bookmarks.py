import csv
import sys
import sqlite3
from collections import namedtuple

from firefed.feature import Feature, output_formats
from firefed.output import info, good
from firefed.util import moz_timestamp


DIRECTORY_TYPE = 2
Bookmark = namedtuple('Bookmark', 'id parent type title guid added last_modified url')


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
        bookmarks = [Bookmark(*row) for row in res]
        # Remove pseudo-bookmarks from list
        bookmarks = [b for b in bookmarks if not str(b.url).startswith('place:')]
        self.build_format(bookmarks)

    def build_tree(self, bookmarks):
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
                walk(child, depth+1)
        for bookmark in bookmarks:
            try:
                parent_guid = bookmark_map[bookmark.parent].guid
            except KeyError:
                continue
            if bookmark.title == '':
                continue
            if bookmark_map[bookmark.parent].guid != 'root________':
                continue
            walk(bookmark)

    def build_list(self, bookmarks):
        for bookmark in bookmarks:
            if not bookmark.url:
                continue
            info('%s\n    %s' % (bookmark.title, bookmark.url))

    def build_csv(self, bookmarks):
        writer = csv.writer(sys.stdout)
        writer.writerow(('title', 'url', 'added', 'last_modified'))
        for b in bookmarks:
            if not b.url:
                continue
            writer.writerow((b.title, b.url, moz_timestamp(b.added), moz_timestamp(b.last_modified)))
