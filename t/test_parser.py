#!/usr/bin/env python
# coding: utf-8

import pytest

from twichat.irc.parser import parse, ParsedReply, MarkedUnexpectedToken, MUT_MARK


def test_can_parse(a_reply):
    parsed_reply = parse(a_reply.text)
    assert isinstance(parsed_reply, ParsedReply)


def test_cant_parse():
    with pytest.raises(MarkedUnexpectedToken) as mut:
        parse("#broken")

    assert f'"#{MUT_MARK}broken"' in str(mut.value)
