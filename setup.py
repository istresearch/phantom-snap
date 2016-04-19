#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup

import re, os


def get_version():
    with open('phantom_snap/__version__.py') as version_file:
        return re.search(r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""",
            version_file.read()).group('version')

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

setup(name='phantom-snap',
    description='Render HTML to an image using PhantomJS with this library \
                  designed to scale for high volume continuous operation.',
    long_description=README,
    author='Andrew Carter',
    author_email='andrew.carter@istresearch.com',
    url='https://github.com/istresearch/phantom-snap',
    keywords=['web', 'html', 'render', 'screenshot', 'phantomjs'],
    license='MIT',
    version=get_version(),
    packages=[
        'phantom_snap'
    ],
    install_requires=[],
    test_suite='nose.collector',
    tests_require=[
        'nose'
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: System",
        "Topic :: System :: Distributed Computing",
        "Topic :: Utilities"
    ]
    )
