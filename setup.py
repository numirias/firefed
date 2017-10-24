from setuptools import setup

setup(
    name='firefed',
    version='0.1',
    description='Firefox profile analyzer',
    url='https://github.com/numirias/firefed',
    author='numirias',
    license='MIT',
    keywords='firefox security privacy',
    packages=['firefed'],
    install_requires=['tabulate', 'colorama'],
)
