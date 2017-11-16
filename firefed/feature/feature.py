import sqlite3
import json
import lz4
from abc import ABC, abstractmethod
from pathlib import Path

from firefed.output import info


def argument(*args, **kwargs):
    def decorator(cls):
        original_add_arguments = cls.add_arguments
        def add_arguments(parser):
            parser.add_argument(*args, **kwargs)
            original_add_arguments(parser)
        cls.add_arguments = add_arguments
        return cls
    return decorator


def output_formats(choices, **kwargs):
    return argument(
        '-f',
        '--format',
        choices=choices,
        help='output format',
        **kwargs,
    )


class NotMozLz4Exception(Exception):
    pass


class Feature(ABC):

    description = '(no description)'
    has_summary = False

    def __init__(self, session, **kwargs):
        self.session = session
        self.__dict__.update(kwargs)

    def __call__(self):
        self.run()

    def add_arguments(parser):
        pass

    @abstractmethod
    def run(self):
        pass

    def profile_path(self, path):
        return Path(self.session.profile) / path

    def load_json(self, path):
        with open(self.profile_path(path)) as f:
            data = json.load(f)
        return data

    def load_sqlite(self, db_path, table, cls):
        def obj_factory(cursor, row):
            dict_ = {}
            for idx, col in enumerate(cursor.description):
                try:
                    new_name = cls._column_map[col[0]]
                except AttributeError:
                    new_name = col[0]
                dict_[new_name] = row[idx]
            return cls(**dict_)
        con = sqlite3.connect(str(self.profile_path(db_path)))
        con.row_factory = obj_factory
        cursor = con.cursor()
        try:
            sql_fields = cls._column_map.keys()
        except AttributeError:
            sql_fields = cls._fields
        result = cursor.execute('SELECT %s FROM %s' %
                                (','.join(sql_fields), table)).fetchall()
        con.close()
        return result

    def load_moz_lz4(self, path):
        with open(self.profile_path(path), 'rb') as f:
            if f.read(8) != b'mozLz40\0':
                raise NotMozLz4Exception('Not Mozilla lz4 format.')
            data = lz4.block.decompress(f.read())
        return data

    def build_format(self, *args, **kwargs):
        getattr(self, 'build_%s' % self.format)(*args, **kwargs)


class SqliteTableFeature(ABC):

    def run(self):
        con = sqlite3.connect(str(self.profile_path(self.db_file)))
        cursor = con.cursor()
        num = cursor.execute(
            'SELECT COUNT(*) FROM %s' % self.table_name).fetchone()[0]
        if hasattr(self, 'format') and self.format != 'csv':
            info(self.num_text % num + '\n')
        if hasattr(self, 'summarize') and self.summarize:
            return
        result = cursor.execute('SELECT %s FROM %s' %
                                (','.join(self.fields), self.table_name)).fetchall()
        con.close()
        self.process_result(result)

    @abstractmethod
    def process_result(self, result):
        pass
