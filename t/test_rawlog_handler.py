#!/usr/bin/env python
# coding: utf-8
# pylint: disable=redefined-outer-name

from io import StringIO
import pytest

from twichat.handlers import RawLog

RS = "\x1e"  # \x1e is the ASCII record separator


@pytest.fixture(scope="module")
def file_rawlog():
    yield RawLog("t/output/raw.log", mode="w")


@pytest.fixture(scope="module")
def ios():
    yield StringIO()


@pytest.fixture(scope="module")
def ios_rawlog(ios):
    yield RawLog(ios, line_ending=RS)


def test_rawlog_handler(a_reply, ios, ios_rawlog, file_rawlog):
    # we don't really test this, but if it doesn't crash, that's feels like a
    # victory. \o/ Hooray us !! \o/
    file_rawlog(a_reply.text)

    gvb = ios.getvalue()
    ios_rawlog(a_reply.text)
    gva = ios.getvalue()
    ll = gva.split(RS)[-2]
    assert len(gva) - len(gvb) == len(a_reply.text) + len(RS)
    assert ll == a_reply.text
