import os

from setuptools import setup, find_packages

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
    author_email=about['__author_email__'],
    license=about['__license__'],
    keywords=about['__keywords__'],
    packages=find_packages(exclude=['tests']),
    install_requires=['colorama', 'lz4', 'requests', 'attrs>=17.4'],
    python_requires='>=3',
    entry_points={
        'console_scripts': [
            'firefed = firefed.__main__:main',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Security',
        'Topic :: Internet :: WWW/HTTP :: Browsers',
    ],
)
