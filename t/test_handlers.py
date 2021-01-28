#!/usr/bin/env python
# coding: utf-8

from twichat.irc.reply import grok
from twichat.handlers import JoinChannel


def test_join_channel(a_reply17, a_reply19, a_reply40):
    g17 = grok(a_reply17)  # NOTICE *** looking you up bro ***
    g19 = grok(a_reply19)  # 001 Welcome
    g40 = grok(a_reply40)  # server MODE :+i

    h = JoinChannel("supz")

    hr17 = h(g17)
    hr19 = h(g19)
    hr40 = h(g40)

    assert not hr17

    for hr in (hr19, hr40):
        assert hr.done
        assert str(hr.send) == "JOIN #supz"
