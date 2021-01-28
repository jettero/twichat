#!/usr/bin/env python
# coding: utf-8

from twichat.irc.reply import grok


def test_leaver(a_reply):
    if "PART" in a_reply.text or "QUIT" in a_reply.text:
        g = grok(a_reply.text)
        assert g.leaver


def test_joiner(a_reply):
    if "JOIN" in a_reply.text:
        g = grok(a_reply.text)
        assert g.joiner
