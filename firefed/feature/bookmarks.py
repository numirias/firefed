import csv
import sys
import sqlite3
from collections import namedtuple

from feature import Feature, output_formats
from output import info, good


Bookmark = namedtuple('Bookmark', 'id parent type title url')
DIRECTORY_TYPE = 2


@output_formats(['tree', 'list', 'csv'], default='tree')
class Bookmarks(Feature):

    def run(self):
        con = sqlite3.connect(self.profile_path('places.sqlite'))
        cursor = con.cursor()
        result = cursor.execute(
            'SELECT b.id, b.parent, b.type, b.title, p.url FROM moz_bookmarks b LEFT JOIN moz_places p ON b.fk = p.id'
        )
        bookmarks = [Bookmark(*row) for row in result]
        # Remove pseudo-bookmarks from list
        bookmarks = [b for b in bookmarks if not str(b.url).startswith('place:')]
        con.close()
        self.build_format(bookmarks)

    def build_tree(self, bookmarks):
        b_map = {b.id: b for b in bookmarks}
        def walk(node, depth=0):
            if node.type == DIRECTORY_TYPE:
                text = good('[%s]') % node.title
                info('%s%s' % (depth*4*' ', text))
            else:
                info('%s- %s' % (depth*4*' ', node.title))
                info('%s%s' % ((depth+1)*4*' ', node.url))

            children = [n for n in bookmarks if n.parent == node.id]
            for child in children:
                walk(child, depth+1)
        for b in bookmarks:
            if b.parent == 1:
                walk(b)

    def build_list(self, bookmarks):
        for bookmark in bookmarks:
            if not bookmark.url:
                continue
            info('%s\n    %s' % (bookmark.title, bookmark.url))

    def build_csv(self, bookmarks):
        writer = csv.writer(sys.stdout)
        writer.writerow(('title', 'url'))
        writer.writerows(((b.title, b.url) for b in bookmarks if b.url))
