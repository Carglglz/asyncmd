#!/usr/bin/env python3

from setuptools import setup
import sys
import os

sys.path.append(os.path.dirname(__file__))
from asyncmd import __version__ as version

setup(
    name="asyncmd",
    version=version,
    description="asyncmd CLI tool",
    url="http://github.com/Crglglz/asyncmd",
    author="Carlos Gil Gonzalez",
    author_email="carlosgilglez@gmail.com",
    license="MIT",
    packages=["asyncmd"],
    zip_safe=False,
    include_package_data=True,
    scripts=["bin/asyncmd"],
    install_requires=[
        "argcomplete>=2.0.0",
        "asyncio_mqtt",
        "pyyaml",
        "tqdm",
        "prompt_toolkit",
    ],
)
