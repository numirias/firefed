from firefed import Session
from firefed.util import make_parser


def main():
    parser = make_parser()
    args = vars(parser.parse_args())
    session = Session(args.pop('profile'))
    session(args.pop('feature'), args)


if __name__ == '__main__':
    main()
