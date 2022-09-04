#!/usr/bin/env python3
import sys
from setuptools import setup, find_packages
from inspect import cleandoc
import sts

long_description = open('README.md', encoding='utf-8').read()

setup(
    name='sts-lib',
    version=sts.__version__,
    description=cleandoc(sts.__doc__),
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=sts.__author__,
    author_email=sts.__author_email__,
    url=sts.__homepage__,
    license=sts.__license__,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        ],
    python_requires='~=3.7',
    packages=find_packages(exclude=['tests']),
    package_data={
        '': [
            'data/config/*.json',
            'data/dictionary/*.txt',
            'data/scheme/*.txt',
            ]
        },
    entry_points={
        'console_scripts': [
            'sts = sts:main',
            ],
        },
    )
