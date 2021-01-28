#!/usr/bin/env python
# coding: utf-8

import asyncio
import logging
import ssl
import certifi

from .msg import PASS, USER, NICK
from ..const import CRLF, WS, TWITCH_HOST, TWITCH_PORT

log = logging.getLogger(__name__)


def make_ssl_context(verify_ssl=True):
    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    if verify_ssl:
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        context.load_verify_locations(certifi.where())
    return context


class IRCConnection:
    reader = writer = closed = context = None
    outgoing_encoding = "utf-8"
    incoming_encoding = "utf-8"

    def __init__(
        self, host=TWITCH_HOST, port=TWITCH_PORT, use_ssl=True, verify_ssl=True
    ):
        if ":" in host:
            self.host, self.port = host.split(":")
        else:
            self.host, self.port = host, port
        if use_ssl:
            self.context = make_ssl_context(verify_ssl=verify_ssl)
        self.closed = True

    async def start(self):
        log.debug("start() connecting to %s:%s", self.host, self.port)
        self.reader, self.writer = await asyncio.open_connection(
            host=self.host, port=self.port, ssl=self.context
        )
        self.closed = False

    def writeline(self, blah):
        # RFC1459 says IRC lines should end with \x0d\x0a, but on most servers
        # they actually end with \x0a only … we'll try to do the right thing
        if self.closed:
            log.debug("writeline() closed, ignored")
            return
        if not isinstance(blah, (bytes, bytearray)):
            blah = str(blah).rstrip(WS) + CRLF
            blah = blah.encode(self.outgoing_encoding)
        self.writer.write(blah)
        asyncio.create_task(self.writer.drain())

    def close(self):
        if self.closed:
            log.debug("close() closed, ignored")
            return
        self.writer.close()
        self.closed = True

    async def readline(self):
        if self.closed:
            log.debug("readline() closed, ignored")
            return
        ret = await self.reader.readline()
        if not ret:
            self.close()
        return ret.decode(self.incoming_encoding).rstrip(WS)

    def register(
        self,
        nick,
        passwd=None,
        username=None,
        realname="M. Incognito",
        servername=None,
        hostname="localhost",
    ):
        """ Tries to produce normal looking messages for PASS, USER, NICK,
            based on sometimes limited input

            sock.register('jettero') → USER who cares stuff here, NICK jettero
            sock.register('jettero', 'oauth:lolololol') → PASS oauth:lololol, USER blah, NICK jettero
        """

        if username is None:
            username = nick
        if realname is None:
            realname = nick
        if servername is None:
            servername = self.host
        if hostname is None:
            hostname = "localhost"

        if passwd is not None:
            log.debug("register() writing PASS to socket")
            self.writeline(PASS(passwd))

        user = USER(
            username, realname=realname, hostname=hostname, servername=servername
        )
        log.debug("register() writing %s to socket", user)
        self.writeline(user)

        nick = NICK(nick)
        log.debug("register() writing %s to socket", nick)
        self.writeline(nick)


async def twitch():
    return await IRCConnection(host=TWITCH_HOST, port=TWITCH_PORT)


# this is mainly just for testing purposes
async def freenode():
    return await IRCConnection(host="irc.freenode.net", port=6697)
