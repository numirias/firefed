# pylint: disable=protected-access
from abc import ABC, abstractmethod
import argparse
from collections import OrderedDict
import csv
import json
import sqlite3
import sys

import attr
from attr import attrib, attrs
import lz4.block

from firefed.output import info


class Argument:
    """Wrapper for an attribute that can be given as a command line argument.

    This class proxies argparse's add_argument() and takes the same arguments.
    Its purpose is to specify a feature attribute that can also be set as a
    command-line argument.
    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    @property
    def default(self):
        """Return the argument default value.

        To determine the value, the argument is passed through a mocked-up
        argument parser. This way, we get defaults even if the feature is
        called directly and not through the CLI.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument(*self.args, **self.kwargs)
        args = vars(parser.parse_args([]))
        _, default = args.popitem()
        return default


arg = Argument


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
        """Load data from sqlite db and return as list of specified objects."""
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
        res = cursor.execute(query).fetchall() # TODO Use generator
        con.close()
        return res

    def load_json(self, path):
        """Load a JSON file from the user profile."""
        with open(self.profile_path(path)) as f:
            data = json.load(f)
        return data

    def load_mozlz4(self, path):
        """Load a Mozilla LZ4 file from the user profile.

        Mozilla LZ4 is regular LZ4 with a custom string prefix.
        """
        with open(self.profile_path(path), 'rb') as f:
            if f.read(8) != b'mozLz40\0':
                raise NotMozLz4Error('Not Mozilla LZ4 format.')
            data = lz4.block.decompress(f.read())
        return data

    @staticmethod
    def csv_from_items(items, stream=None):
        """Write a list of items to stream in CSV format.

        The items need to be attrs-decorated.
        """
        cls = items[0].__class__
        if stream is None:
            stream = sys.stdout
        fields = [f.name for f in attr.fields(cls)]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows([attr.asdict(x) for x in items])

    def profile_path(self, path):
        """Return path from current profile."""
        return self.session.profile / path


@attrs
class Feature(FeatureHelpersMixin, ABC):
    """Abstract base class for features.

    All features derive from this class and will be automatically registered by
    the argument parser.

    Features must use an @attrs class decorator and declare attributes on the
    class level via attrib(), not inside an __init__ function. Attributes that
    should be settable as command-line arguments, should use arg().
    """
    cli_args = None
    summary = None
    session = attrib()

    def __init_subclass__(cls):
        """Initialize feature subclass with the appropriate arguments.

        If the feature has formatters, a format argument is added. All arg()
        attributes are registered as command-line arguments and converted to
        attrib().
        """
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
        if cls.summarizable():
            cls.summary = arg(
                '-s', '--summary',
                action='store_true',
                help='summarize results',
            )
        cls._convert_arg_attribues()

    def __call__(self):
        """Execute the feature.

        First, prepare() is called. Then either summarize() or run() is called
        depending on the configuration.
        """
        info('Profile: %s', self.session.profile)
        info('Feature: %s\n', self.__class__.__name__)
        self.prepare()
        if self.summary:
            self.summarize()
        else:
            self.run()

    @classmethod
    def description(cls):
        """Return a description of the feature (used in the help message).

        If not overwitten, the description is the first line of the docstring.
        """
        try:
            return cls.__doc__.split('\n')[0]
        except AttributeError:
            return '(no description)'

    @classmethod
    def _convert_arg_attribues(cls):
        """Convert all command line arguments to proper attributes.

        Convert all arg() attributes to attrib() and register them as CLI args.
        """
        # TODO Do we really need to convert explicitly?
        attrs = {a: getattr(cls, a, None) for a in dir(cls)}
        cli_args = {k: v for k, v in attrs.items() if isinstance(v, Argument)}
        cls.cli_args = cli_args
        for k, v in cli_args.items():
            setattr(cls, k, attrib(default=v.default))

    @classmethod
    def formatters(cls):
        """Return all output formatters of the class.

        Return a dict of all methods with an _output_format attribute.
        """
        return {m._output_format['name']: m for m in vars(cls).values() if
                callable(m) and getattr(m, '_output_format', None)}

    @classmethod
    def feature_map(cls):
        """Create an ordered mapping of all feature names and their classes."""
        return OrderedDict(
            sorted(
                ((c.__name__.lower(), c) for c in cls.__subclasses__()),
                key=(lambda x: x[0])
            )
        )

    @classmethod
    def summarizable(cls):
        """Return whether the feature has overridden the summary method."""
        return getattr(cls, 'summarize') is not getattr(Feature, 'summarize')

    def build_format(self):
        """Call the configured formatter method.

        This method is usually called inside run() to automatically evoke the
        correct formatter according to the configuration.
        """
        self.formatters()[self.format](self) # TODO make _formatters underscore

    def prepare(self):
        """This method is called before run() or summarize()."""
        pass

    def summarize(self):
        """Summarize the results of executing the feature."""
        pass

    @abstractmethod
    def run(self):
        """Run the feature."""
        pass
