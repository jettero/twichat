#!/usr/bin/env python
# coding: utf-8

from collections import namedtuple

ReplyLine = namedtuple("ReplyLine", ["testfile_lineno", "reply_no", "text"])


def get_test_lines():
    ret = list()
    with open("t/test-lines", "r") as fh:
        l = 0
        r = -1
        for line in fh:
            l += 1
            line = line.rstrip()
            if line.startswith("#") or not line:
                continue
            r += 1
            # NOTE: we wrap this in a pointless object so the pytest -v results
            # trigger a tragic line-wrap mess
            #
            # t/test_conftest.py::test_a_reply[:palmereldritch3s.tmi.twitch.tv
            # 353 palmereldritch3s = #palmereldritch3s :palmereldritch3s\n]
            # PASSED [ 50%]
            #
            # vs
            #
            # t/test_conftest.py::test_a_reply[a_reply7] PASSED [ 53%]
            ret.append(ReplyLine(l, r, line))
    return ret


TEST_LINES = tuple(get_test_lines())


def generate_reply_names():
    for idx, item in enumerate(TEST_LINES):
        yield f"a_reply{idx}", item.text


def populate_globals():
    g = globals()
    for name, value in generate_reply_names():
        g[name] = value


del get_test_lines, namedtuple
