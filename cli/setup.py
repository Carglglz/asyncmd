#!/usr/bin/env python3
# @Author: carlosgilgonzalez
# @Date:   2019-07-11T23:29:40+01:00
# @Last modified by:   carlosgilgonzalez
# @Last modified time: 2019-07-14T13:48:30+01:00

from setuptools import setup

setup(
    name="asyncmd",
    version="0.0.1",
    description="asyncmd CLI tool",
    url="http://github.com/Crglglz/asyncmd",
    author="Carlos Gil Gonzalez",
    author_email="carlosgilglez@gmail.com",
    license="MIT",
    packages=["asyncmd"],
    zip_safe=False,
    include_package_data=True,
    scripts=["bin/asyncmd"],
)
