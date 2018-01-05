# pylint: disable=protected-access
from abc import ABC, abstractmethod
import argparse
from collections import OrderedDict
import csv
import json
from pathlib import Path
import sqlite3
import sys

import attr
from attr import attrib, attrs
import lz4.block

from firefed.output import info


class arg:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

def formatter(name, default=False):
    def decorator(func):
        func._output_format = dict(name=name, default=default)
        return func
    return decorator

class NotMozLz4Error(Exception):
    pass

class FeatureHelpersMixin:

    def load_sqlite(self, db, query=None, table=None, cls=None,
                    column_map=None):
        if column_map is None:
            column_map = {}
        db_path = self.profile_path(db)
        if not db_path.exists():
            raise FileNotFoundError()
        def obj_factory(cursor, row):
            dict_ = {}
            for idx, col in enumerate(cursor.description):
                new_name = column_map.get(col[0], col[0])
                dict_[new_name] = row[idx]
            return cls(**dict_)
        con = sqlite3.connect(str(db_path))
        con.row_factory = obj_factory
        cursor = con.cursor()
        if not query:
            columns = [f.name for f in attr.fields(cls)]
            for k, v in column_map.items():
                columns[columns.index(v)] = k
            query = 'SELECT %s FROM %s' % (','.join(columns), table)
        res = cursor.execute(query).fetchall()
        con.close()
        return res

    def load_json(self, path):
        with open(self.profile_path(path)) as f:
            data = json.load(f)
        return data

    def load_mozlz4(self, path):
        with open(self.profile_path(path), 'rb') as f:
            if f.read(8) != b'mozLz40\0':
                raise NotMozLz4Error('Not Mozilla lz4 format.')
            data = lz4.block.decompress(f.read())
        return data

    @staticmethod
    def csv_from_items(items, stream=None):
        cls = items[0].__class__
        if stream is None:
            stream = sys.stdout
        fields = [f.name for f in attr.fields(cls)]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows([attr.asdict(x) for x in items])

    def profile_path(self, path):
        return Path(self.session.profile) / path


def get_default(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument(*arg.args, **arg.kwargs)
    args = vars(parser.parse_args([]))
    _, default = args.popitem()
    return default


@attrs
class Feature(FeatureHelpersMixin, ABC):

    cli_args = None
    description = '(no description)'
    session = attrib()
    summary = arg(
        '-s', '--summary',
        action='store_true',
        help='summarize results',
    )

    def __call__(self):
        info('Profile: %s', self.session.profile)
        info('Feature: %s\n', self.__class__.__name__)
        if hasattr(self, 'prepare'):
            self.prepare()
        if self.summary:
            self.summarize()
        else:
            self.run()

    def __init_subclass__(cls):
        formatters = cls.formatters()
        if formatters:
            choices = formatters.keys()
            default_format = next((name for name, m in formatters.items() if
                                   m._output_format['default']), None)
            cls.format = arg(
                '-f',
                '--format',
                choices=choices,
                help='output format',
                default=default_format,
            )
        cls._convert_arg_attribues()

    @classmethod
    def _convert_arg_attribues(cls):
        """Convert all command line arguments to proper attributes.

        Convert all arg() attributes to attrib() and register them as CLI args.
        """
        attribs = {a: getattr(cls, a, None) for a in dir(cls)}
        cli_args = {k: v for k, v in attribs.items() if isinstance(v, arg)}
        cls.cli_args = cli_args
        for k, v in cli_args.items():
            default = get_default(v)
            setattr(cls, k, attrib(default=default))

    @classmethod
    def formatters(cls):
        """Return all formatters in the class.

        Return a dict of all methods with an _output_format attribute.
        """
        return {m._output_format['name']: m for m in vars(cls).values() if
                callable(m) and getattr(m, '_output_format', None)}

    @classmethod
    def feature_map(cls):
        return OrderedDict(
            sorted(
                ((c.__name__.lower(), c) for c in cls.__subclasses__()),
                key=(lambda x: x[0])
            )
        )

    def build_format(self):
        self.formatters()[self.format](self) # TODO make _formatters underscore

    @abstractmethod
    def summarize(self):
        pass

    @abstractmethod
    def run(self):
        pass
