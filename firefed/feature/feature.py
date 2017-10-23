import os
import sqlite3


class Feature:

    def __init__(self, firefed):
        self.ff = firefed

    def __call__(self, args):
        self.run(args)

    def run(self, args):
        raise NotImplementedError('Features need to implement run()!')

    def profile_path(self, fn):
        return os.path.join(self.ff.profile_dir, fn)


class SqliteTableFeature:

    def run(self, args):
        con = sqlite3.connect(self.profile_path(self.db_file))
        cursor = con.cursor()
        num = cursor.execute('SELECT COUNT(*) FROM %s' % self.table_name).fetchone()[0]
        print(self.num_text % num + '\n')
        if args.summarize:
            return
        result = cursor.execute('SELECT %s FROM %s' % (','.join(self.fields), self.table_name)).fetchall()
        self.process_result(result)

    def process_result(self, result):
        raise NotImplementedError()
