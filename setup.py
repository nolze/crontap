#!/usr/bin/env python

from setuptools import find_packages, setup

import crontap
version = crontap.__version__

__author__ = "nolze"

setup(
    name="crontap",
    version=version,
    description="crontap : crontab for Humans",
    long_description=open("README.md").read(),
    license="GPLv3",
    url="https://github.com/nolze/crontap",
    author="nolze",
    classifiers=[
        "Environment :: Console",
        "Programming Language :: Python",
    ],
    packages=['crontap'],
    package_data={
        '': [
            'settings.yaml',
            'module_template/*',
        ]
    },
    entry_points={
        "console_scripts": [
            "crontap = crontap.crontap:cli",
        ]
    },
    install_requires=[
        "Click >= 3.0",
        "PyYAML >= 3.11",
        "plaintable >= 0.1.1",
        ],
    zip_safe=False
)
