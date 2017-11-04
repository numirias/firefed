import os
import sqlite3
import json
import lz4


class Feature:

    description = '(no description)'

    def __init__(self, firefed):
        self.ff = firefed
        self.args = None

    def __call__(self, args):
        self.args = args
        self.run()

    def run(self):
        raise NotImplementedError('Features need to implement run()!')

    def profile_path(self, path):
        return os.path.join(self.ff.profile_dir, path)

    def load_json(self, path):
        with open(self.profile_path(path)) as f:
            data = json.load(f)
        return data

    def load_sqlite(self, db_path, table, cls):
        def obj_factory(cursor, row):
            dict_ = {}
            for idx, col in enumerate(cursor.description):
                new_name = cls._column_map[col[0]]
                dict_[new_name] = row[idx]
            return cls(**dict_)
        con = sqlite3.connect(self.profile_path(db_path))
        con.row_factory = obj_factory
        cursor = con.cursor()
        result = cursor.execute('SELECT %s FROM %s' %
                                (','.join(cls._column_map), table)).fetchall()
        con.close()
        return result

    def load_moz_lz4(self, path):
        with open(self.profile_path(path), 'rb') as f:
            if f.read(8) != b'mozLz40\0':
                raise Exception('Not Mozilla lz4 format.')
            data = lz4.block.decompress(f.read())
        return data

    def add_arguments(parser):
        pass


class SqliteTableFeature:

    def run(self):
        con = sqlite3.connect(self.profile_path(self.db_file))
        cursor = con.cursor()
        num = cursor.execute(
            'SELECT COUNT(*) FROM %s' % self.table_name).fetchone()[0]
        print(self.num_text % num + '\n')
        if self.args.summarize:
            return
        result = cursor.execute('SELECT %s FROM %s' %
                                (','.join(self.fields), self.table_name)).fetchall()
        con.close()
        self.process_result(result)

    def process_result(self, result):
        raise NotImplementedError()
