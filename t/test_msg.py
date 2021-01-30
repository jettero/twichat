#!/usr/bin/env python
# coding: utf-8

import pytest
from twichat.irc.msg import Message, NICK, TargetMessage


def test_msg_basics():
    assert str(Message("M0")) == "M0"
    assert str(Message("M1", "one")) == "M1 one"
    assert str(Message("M2", "one", "two")) == "M2 one :two"
    assert (
        str(Message("M3", "one", "two", "this is three")) == "M3 one two :this is three"
    )

    with pytest.raises(ValueError):
        Message("M4", "one has a space", "two")


def test_outgoing_msg_examples():
    n0 = NICK("namehere")  # please change my name to "namehere"
    n1 = Message("nick", "namehere")  # same thing

    assert str(n0) == "NICK namehere"
    assert str(n1) == "NICK namehere"

    t0 = TargetMessage("#channelname", "this is my silly message")
    t1 = Message("PRIVMSG", "#channelname", "this is my silly message")

    assert str(t0) == "PRIVMSG #channelname :this is my silly message"
    assert str(t1) == "PRIVMSG #channelname :this is my silly message"


def test_msg_tags():
    # AFAIK, this isn't actually how you send a message that's read; the tags used by Twitch IRC
    # appear to come from the server in the replies and you don't normally send them? I think?
    # But there's limited support for tags in case they're actually needed somehow.
    m0 = Message(
        "privmsg", "#channel", "this is a red message", color="#FF0000", scooby="snacks"
    )
    assert (
        str(m0)
        == "@color=#FF0000;scooby=snacks PRIVMSG #channel :this is a red message"
    )
