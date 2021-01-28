#!/usr/bin/env python
# coding: utf-8

from twichat.irc.reply import grok


def test_join_namelist_43(a_reply43):
    g43 = grok(a_reply43)

    assert len(g43.nicks) == 1
    assert g43.nicks[0].nick == "just_testing_som"
    assert g43.nicks[0].op is True
    assert g43.channel == "#twichat"
    assert g43.origin.name == "tepper.freenode.net"


def test_join_namelist_55(a_reply55):
    g55 = grok(a_reply55)

    assert len(g55.nicks) == 2
    assert g55.nicks[0].nick == "just_testing_som"
    assert g55.nicks[1].nick == "jettero"
    assert g55.nicks[0].op is False
    assert g55.nicks[0].op is False
    assert g55.channel == "#twichat"
    assert g55.origin.name == "tepper.freenode.net"


def test_join_topic_5354(a_reply53, a_reply54):
    g53 = grok(a_reply53)

    assert g53.topic == "lol this is a topic"
    assert g53.channel == "#twichat"

    g54 = grok(a_reply54)
    assert g54.channel == "#twichat"
    assert g54.nick == "jettero"
    assert "jettero!" in g54.author
    assert g54.mtime == "Sun Dec 13 17:15:18 2020"
