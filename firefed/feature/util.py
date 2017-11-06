from collections import OrderedDict

from feature import Feature


def feature_map():
    return OrderedDict(
        sorted((m.__name__.lower(), m) for m in Feature.__subclasses__())
    )
