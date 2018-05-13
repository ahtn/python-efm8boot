#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

from setuptools import setup, find_packages
from codecs import open
from os import path

__version__ = '0.0.5'

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

install_requires = [x.strip() for x in all_reqs if 'git+' not in x]
dependency_links = [x.strip().replace('git+', '') for x in all_reqs if x.startswith('git+')]

setup(
    name='efm8boot',
    version=__version__,
    description='A python package for working with efm8 bootloaders.',
    long_description=long_description,
    url='https://github.com/ahtn/efm8boot',
    download_url='https://github.com/ahtn/efm8boot/tarball/' + __version__,
    license='BSD',
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'Programming Language :: Python :: 3',
    ],
    keywords='efm8 bootloader 8051',
    packages=find_packages(exclude=['docs', 'tests*']),
    scripts = ['scripts/efm8boot-cli.py'],
    include_package_data=True,
    author='jem',
    install_requires=install_requires,
    dependency_links=dependency_links,
    author_email='jem@seethis.link'
)
