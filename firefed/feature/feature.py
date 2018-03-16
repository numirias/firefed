# pylint: disable=protected-access
from abc import ABC, abstractmethod
import argparse
from collections import OrderedDict
import csv
import errno
import json
import os
from pathlib import PurePath
import sqlite3
import sys

import attr
from attr import attrib, attrs
import lz4.block


def arg(*args, **kwargs):
    """Return an attrib() that can be fed as a command-line argument.

    This function is a wrapper for an attr.attrib to create a corresponding
    command line argument for it. Use it with the same arguments as argparse's
    add_argument().

    Example:

    >>> @attrs
    ... class MyFeature(Feature):
    ...     my_number = arg('-n', '--number', default=3)
    ...     def run(self):
    ...         print('Your number:', self.my_number)

    Now you could run it like `firefed myfeature --number 5`.
    """
    metadata = {'arg_params': (args, kwargs)}
    return attrib(default=arg_default(*args, **kwargs), metadata=metadata)


def arg_default(*args, **kwargs):
    """Return default argument value as given by argparse's add_argument().

    The argument is passed through a mocked-up argument parser. This way, we
    get default parameters even if the feature is called directly and not
    through the CLI.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(*args, **kwargs)
    args = vars(parser.parse_args([]))
    _, default = args.popitem()
    return default


def formatter(name, default=False):
    """Decorate a Feature method to register it as an output formatter.

    All formatters are picked up by the argument parser so that they can be
    listed and selected on the CLI via the -f, --format argument.
    """
    def decorator(func):
        func._output_format = dict(name=name, default=default)
        return func
    return decorator


class NotMozLz4Error(Exception):
    """Raised when an LZ4 file doesn't use Mozilla's proprietary prefix."""


class FeatureHelpersMixin:
    """Helper methods to be used by features which simplify common tasks."""

    def load_sqlite(self, db, query=None, table=None, cls=None,
                    column_map=None):
        """Load data from sqlite db and return as list of specified objects."""
        if column_map is None:
            column_map = {}
        db_path = self.profile_path(db, must_exist=True)

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
        cursor.execute(query)
        while True:
            item = cursor.fetchone()
            if item is None:
                break
            yield item
        con.close()

    def load_json(self, path):
        """Load a JSON file from the user profile."""
        with open(self.profile_path(path, must_exist=True),
                  encoding='utf-8') as f:
            data = json.load(f)
        return data

    def load_mozlz4(self, path):
        """Load a Mozilla LZ4 file from the user profile.

        Mozilla LZ4 is regular LZ4 with a custom string prefix.
        """
        with open(self.profile_path(path, must_exist=True), 'rb') as f:
            if f.read(8) != b'mozLz40\0':
                raise NotMozLz4Error('Not Mozilla LZ4 format.')
            data = lz4.block.decompress(f.read())
        return data

    def load_json_mozlz4(self, path):
        return json.loads(self.load_mozlz4(path), encoding='utf-8')

    def write_mozlz4(self, path, data):
        compressed = lz4.block.compress(bytes(data, 'utf-8'))
        with open(self.profile_path(path), 'wb') as f:
            f.write(b'mozLz40\0' + compressed)

    def write_json_mozlz4(self, path, data):
        self.write_mozlz4(path, json.dumps(data))

    @staticmethod
    def csv_from_items(items, stream=None):
        """Write a list of items to stream in CSV format.

        The items need to be attrs-decorated.
        """
        items = iter(items)
        first = next(items)
        cls = first.__class__
        if stream is None:
            stream = sys.stdout
        fields = [f.name for f in attr.fields(cls)]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow(attr.asdict(first))
        writer.writerows((attr.asdict(x) for x in items))

    def profile_path(self, path, must_exist=False):
        """Return path from current profile."""
        full_path = self.session.profile / path
        if must_exist and not full_path.exists():
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                PurePath(full_path).name,
            )
        return full_path


@attrs
class Feature(FeatureHelpersMixin, ABC):
    """Abstract base class for features.

    All features derive from this class and will be automatically registered by
    the argument parser.

    Features must use an @attrs class decorator and declare attributes on the
    class level via attrib(), not inside an __init__ function. Attributes that
    should be settable as command-line arguments, should use arg().
    """
    format = None
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
            default_format = next((name for name, m in formatters.items()
                                   if m._output_format['default']), None)
            cls.format = arg(
                '-f', '--format',
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

    def __call__(self):
        """Execute the feature.

        First, prepare() is called. Then either summarize() or run() is called
        depending on the configuration.
        """
        self.session.logger.info('Profile: %s', self.session.profile)
        self.session.logger.info('Feature: %s', self.__class__.__name__)
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
    def cli_args(cls):
        """Generate argument tuples to be used on the CLI."""
        for field in attr.fields(cls):
            try:
                args, kwargs = field.metadata['arg_params']
            except KeyError:
                continue
            kwargs = kwargs.copy()
            kwargs['dest'] = field.name
            yield (args, kwargs)

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
        features = cls.__subclasses__()
        names_and_features = ((f.__name__.lower(), f) for f in features)
        return OrderedDict(sorted(names_and_features, key=(lambda x: x[0])))

    @classmethod
    def summarizable(cls):
        """Return whether the feature has overridden the summary method."""
        return getattr(cls, 'summarize') is not getattr(Feature, 'summarize')

    def build_format(self):
        """Call the configured formatter method.

        This method is usually called by a feature inside run() to evoke the
        correct formatter according to the --format argument.
        """
        self.formatters()[self.format](self)

    def prepare(self):
        """This method is called before run() or summarize()."""

    def summarize(self):
        """Summarize the results of executing the feature."""
        pass # pragma: no cover

    @abstractmethod
    def run(self):
        """Run the feature."""
