#!/usr/bin/env python
# coding: utf-8


def test_a_reply(a_reply):
    assert a_reply.testfile_lineno > 0
    assert len(a_reply.text) > 0
    assert a_reply.text[0] != "#"


def test_a_reply0(a_reply0):
    assert "GLHF" in a_reply0


def test_a_reply1(a_reply11):
    assert "PONG" in a_reply11
