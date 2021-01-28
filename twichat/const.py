#!/usr/bin/env python
# coding: utf-8

import os
import uuid

CRLF = "\x0d\x0a"
WS = "\x20\x09" + CRLF

TWITCH_HOST = "irc.chat.twitch.tv"
TWITCH_PORT = 6697

INSTALL_DIR = os.path.dirname(__file__)
PYTHON_DIR = os.path.dirname(os.__file__)

UUID = uuid.uuid1()

del os
del uuid
