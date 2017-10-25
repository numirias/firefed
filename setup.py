import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(here, 'firefed', '__version__.py'), 'r') as f:
    exec(f.read(), about)

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    url=about['__url__'],
    author=about['__author__'],
    license=about['__license__'],
    keywords=about['__keywords__'],
    packages=['firefed'],
    install_requires=['tabulate', 'colorama'],
)
