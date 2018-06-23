#!/usr/bin/env python
from setuptools import setup
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(__file__))
from stir import __version__

long_description = ""
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="stir",
    version = __version__,
    description = "A simple merging package manager for microservices",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    author = "Aaron Meier",
    author_email = 'webgovernor@gmail.com',
    packages = ["stir"],
    package_dir={"stir":"stir"},
    scripts=["stir/scripts/stir"],
    url = "https://github.com/nullism/stir",
    license = 'MIT',
    install_requires = ["cryptography"],
    provides = ["stir"]
)