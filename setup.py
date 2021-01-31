#!/usr/bin/env python
# pylint: disable=attribute-defined-outside-init,import-outside-toplevel

import sys
import os
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
REQS = os.path.join(THIS_DIR, "requirements.txt")


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ""

    def run_tests(self):
        import shlex
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


def reqs(file=REQS):
    with open(file, "r") as fh:
        yield from fh


setup(
    name="twichat",
    use_scm_version={
        "write_to": "twichat/version.py",
        # NOTE: use ./setup.py --version to regenerate version.py and print the
        # computed version
    },
    description="A really lightweight IRC client API with Twitch.tv in mind.",
    author="Paul Miller",
    author_email="paul@jettero.pl",
    url="https://github.com/jettero/twichat",
    tests_require=["pytest",],
    cmdclass={"test": PyTest},
    packages=find_packages(),
    setup_requires=["setuptools_scm"],
    install_requires=reqs(),
)
