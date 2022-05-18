#!/usr/bin/env python


import os
from setuptools import setup

import ggeocoder

setup(
    name='ggeocoder',
    version=ggeocoder.VERSION,
    author='Aaron Madison',
    url='https://github.com/imtapps/ggeocoder',
    description='A Python library for working with Google Geocoding API V3.',
    long_description=open(
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: BSD License',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='google maps api v3 geocode geocoding geocoder reverse',
    license='BSD License',
)
