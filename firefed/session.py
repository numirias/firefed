import logging

import attr
from attr import attrs, attrib

from firefed.__version__ import __title__


@attrs
class Session:

    profile = attrib()
    logger = attrib(default=attr.Factory(lambda x: x.make_logger(),
                                         takes_self=True))
    verbosity = attrib(default=0)

    def __attrs_post_init__(self):
        if self.verbosity > 0:
            self.logger.setLevel(logging.INFO)

    @staticmethod
    def make_logger():
        logger = logging.getLogger(__title__)
        logger.setLevel(logging.ERROR)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
