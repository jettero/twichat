#!/usr/bin/env python
# pylint: disable=attribute-defined-outside-init,import-outside-toplevel

import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


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


with open("requirements.txt", "r") as fh:
    ireqs = list(fh)

with open("test_requirements.txt", "r") as fh:
    treqs = list(fh) + ireqs

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
    cmdclass={"test": PyTest},
    packages=find_packages(),
    tests_require=treqs,
    setup_requires=["setuptools_scm"],
    install_requires=ireqs,
)
