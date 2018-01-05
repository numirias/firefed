import logging

import attr

from firefed.output import logger


@attr.s
class Session:

    profile = attr.ib()
    verbosity = attr.ib(default=0)

    def __attrs_post_init__(self):
        if self.verbosity > 0:
            logger.setLevel(logging.INFO)
