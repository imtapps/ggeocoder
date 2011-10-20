#!/usr/bin/env python


import os
from distutils.core import setup

import ggeocoder

setup(
    name='ggeocoder',
    version=ggeocoder.VERSION,
    author='Aaron Madison',
    url='https://github.com/imtapps/ggeocoder',
    description='A Python library for working with Google Geocoding API V3.',
    long_description=file(
        os.path.join(os.path.dirname(__file__), 'README.rst')
    ).read(),
    py_modules=['ggeocoder'],
    provides=['ggeocoder'],
    tests_require=['mock'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='google maps ajax api geocode geocoding address gps json validation formatting',
    license='Lesser General Public License v3',
)