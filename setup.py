import codecs
import os.path

import sys
from setuptools import setup, find_packages

from kea_exporter import __PROJECT__, __VERSION__


if sys.argv[-1] == "publish":
    os.system("python setup.py sdist bdist_wheel upload")
    sys.exit()

here = os.path.abspath(os.path.dirname(__file__))


# use README as long description
with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as handle:
    long_description = handle.read()

# required dependencies
required = [
    'click>=6.7',
    'prometheus_client>=0.1.1',
    'hjson>=3.0.1',
    'inotify>=0.2.9'
]


setup(
    name=__PROJECT__,
    version=__VERSION__,
    description='Export Kea Metrics in the Prometheus Exposition Format',
    long_description=long_description,
    author='Martin Weinelt',
    author_email='martin+keaexporter@linuxlounge.net',
    url='https://www.github.com/mweinelt/kea-exporter',
    license='MIT',
    install_requires=required,
    packages=find_packages(),
    entry_points={
        'console_scripts': ['kea-exporter=kea_exporter.__main__:cli']
    },
)
