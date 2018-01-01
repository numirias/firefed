import argparse

import firefed.__version__ as version

from firefed import Session
from firefed.util import profile_dir_type
from firefed.feature import Feature
from firefed import util


def main():
    args = util.parse_args()
    session = Session(args.pop('profile'), args.pop('verbosity'))
    feature = Feature.feature_map()[args.pop('feature')]
    feature(session, **args)()


if __name__ == '__main__':
    main()
