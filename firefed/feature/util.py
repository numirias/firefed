from collections import OrderedDict
from datetime import datetime

from feature import Feature


def feature_map():
    return OrderedDict(
        sorted((m.__name__.lower(), m) for m in Feature.__subclasses__())
    )

def moz_datetime(ts):
    return datetime.fromtimestamp(moz_timestamp(ts))

def moz_timestamp(ts):
    return ts // 1000000

