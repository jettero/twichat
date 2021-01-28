#!/usr/bin/env python
# coding: utf-8

import re
from twichat.irc.reply import grok, Arrive, Reply, ParsedReply


def test_join7(a_reply7):
    # ":palmereldritch3s!palmereldritch3s@palmereldritch3s.tmi.twitch.tv JOIN #palmereldritch3s"
    assert "JOIN #palmereldritch3s" in a_reply7

    reply = grok(a_reply7)
    assert bool(reply)
    assert isinstance(reply, ParsedReply)
    assert isinstance(reply, Reply)
    assert isinstance(reply, Arrive)
    assert reply.channel == "#palmereldritch3s"
    assert reply.joiner == "palmereldritch3s"


def test_joinz(a_reply):
    a_reply = a_reply.text
    m = re.search(r"^:(?P<joiner>[^\s!@]+).+?JOIN\s+(?P<chan>#\S+)", a_reply)

    if m:
        joiner, channel = m.groups()
        assert f"JOIN {channel}" in a_reply

        reply = grok(a_reply)
        assert bool(reply)
        assert isinstance(reply, ParsedReply)
        assert isinstance(reply, Reply)
        assert isinstance(reply, Arrive)
        assert reply.channel == channel
        assert reply.joiner == joiner

    else:
        reply = grok(a_reply)
        assert bool(reply)
        assert isinstance(reply, ParsedReply)
        assert isinstance(reply, Reply)
        assert not isinstance(reply, Arrive)
        assert "JOIN" not in a_reply
