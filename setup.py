#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='restless',
    version='1.0.0',
    description='Simplistic RESTful API miniframework.',
    author='Daniel Lindsley',
    author_email='daniel@toastdriven.com',
    url='http://github.com/toastdriven/restless/',
    long_description=open('README.rst', 'r').read(),
    packages=[
        'restless',
    ],
    requires=[
        'six(>=1.4.0)',
    ],
    install_requires=[
        'six>=1.4.0',
    ],
    tests_require=[
        'mock',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities'
    ],
)
