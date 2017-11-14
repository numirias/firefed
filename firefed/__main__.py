import argparse

from firefed import Firefed
from firefed.util import make_parser


def main():
    parser = make_parser()
    args = parser.parse_args()
    Firefed(args)


if __name__ == '__main__':
    main()
