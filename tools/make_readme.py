"""Update documentation in readme.

This tool writes the help texts to the README.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / '../firefed'))  # noqa: E402
from firefed.util import make_parser
from firefed.feature import Feature


readme_path = 'README.md'


def add_section(text, section, name):
    marker = '<!--{name}-{pos}-->\n'
    start = marker.format(name=name, pos='start')
    end = marker.format(name=name, pos='end')
    text_pre, rest = text.split(start)
    _, text_post = rest.split(end)
    return text_pre + start + section + end + text_post


def main():
    with open(readme_path) as f:
        text = f.read()

    parser = make_parser()
    usage_stub = '```\n$ firefed -h\n{help}```\n'
    usage_text = usage_stub.format(help=parser.format_help())

    sub_cmds = parser._subparsers._group_actions[0].choices
    features_stub = '### {name}\n\n{description}\n\n```\n{help}```\n\n'
    features = Feature.feature_map()
    features_text = ''
    for name, cmd in sub_cmds.items():
        feature = features[name]
        features_text += features_stub.format(
            name=feature.__name__,
            description=feature.description(),
            help=cmd.format_help(),
        )

    text = add_section(text, usage_text, 'usage')
    text = add_section(text, features_text, 'features')

    with open(readme_path, 'w') as f:
        f.write(text)
    print('Commands written to "%s".' % readme_path)


if __name__ == '__main__':
    main()
