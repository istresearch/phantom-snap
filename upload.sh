#!/bin/bash
# Script to build the phantom-snap distribution, and push to pypi

python setup.py sdist
twine upload dist/phantom-snap-*.tar.gz
rm -rf dist/*