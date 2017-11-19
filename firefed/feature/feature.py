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

def sqlite_data(db, table, columns):
    def decorator(func):
        def wrapper(obj):
            db_path = obj.profile_path(db)
            if not db_path.exists():
                print(db)
                raise FileNotFoundError()
            con = sqlite3.connect(str(db_path))
            cursor = con.cursor()
            res = cursor.execute('SELECT %s FROM %s' %
                                 (','.join(columns), table)).fetchall()
            con.close()
            func(obj, res)
        return wrapper
    return decorator


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

    def exec_sqlite(self, db_path, query):
        con = sqlite3.connect(str(self.profile_path(db_path)))
        cursor = con.cursor()
        res = list(cursor.execute(query))
        con.close()
        return res

    def load_mozlz4(self, path):
        with open(self.profile_path(path), 'rb') as f:
            if f.read(8) != b'mozLz40\0':
                raise NotMozLz4Exception('Not Mozilla lz4 format.')
            data = lz4.block.decompress(f.read())
        return data

    def build_format(self, *args, **kwargs):
        getattr(self, 'build_%s' % self.format)(*args, **kwargs)
