#!/usr/bin/env python
# coding: utf-8

import os
from abc import abstractmethod, ABC
from .irc.msg import JOIN, PONG

from .const import WS


class HandlerResult:
    """
    A standard container for handler results. The defaults are below:

        res = HandlerResult(
            send=None,
            done=False,
            stop_handles=False,
            stop_mainloop=False)

    send :- a string or object that can be stringified with str(), or a list of
            them to send more than one thing to the irc server.

            from twichat.irc.msg import JOIN
            send1 = JOIN('blah')
            send2 = 'JOIN #blah' # pretty much the same as the above
            # or maybe join two channels
            send3 = [ JOIN('blah'), JOIN('bleak') ]

    done :- tell the mainloop the handler is done, meaning it should not be
            given further messages. Note that the twichat.loop.TWILoop object
            (at the time of this writing anyway) removes the handler from its
            internal list and never adds it back after session close.

            So any restart of the loop would then be missing a handler that
            had announced it was 'done'.

    stop_handles :- tell the mainloop this handler has handled the message. No
                    further processing should take place with it.

    stop_mainloop :- tell the mainloop we're done with this connection. The
                     mainloop will close the IRC connection and terminate if
                     this result attribute evaluates as true.
    """

    def __init__(self, send=None, done=False, stop_handles=False, stop_mainloop=False):
        self.send = send
        self.done = done
        self.stop_handles = stop_handles
        self.stop_mainloop = stop_mainloop


# NOTE: There's a loose convention in this file that if a handler has the word
# 'Handler' in its name, it's not meant to be instanciated directly; it's
# abstract. This, of course, does not apply to the HandlerResult, which isn't a
# Handler at all, just a container.


class BaseHandler(ABC):
    @abstractmethod
    def accept(self, reply):
        return "something to send"

    def __call__(self, reply):
        if ok_send := self.accept(reply):
            return HandlerResult(send=ok_send)


class RawHandler(ABC):
    """
    Handles raw messages (strings, not bytes) sent by the IRC server.

    Note that this class is really just a nickname for BaseHandler. It's meant
    to be used in if blocks like this:

        if isinstance(handler, RawHandler):
            handler(raw_message)
    """

    @abstractmethod
    def __call__(self, message):
        pass


class SendRawHandler(ABC):
    """
    Handles raw outgoing messages sent from bots or users.
    """

    @abstractmethod
    def __call__(self, message):
        pass


class ReplyHandler(BaseHandler):
    """
    Handles messages sent by the IRC server parsed into reply objects.

    Note that this class is really just a nickname for BaseHandler. It's meant
    to be used in if blocks like this:

        if isinstance(handler, ReplyHandler):
            handler(reply_object)
    """


class WaitSendOnceHandler(ReplyHandler):
    """
    A ReplyHandler that only fires one time. That is, if a message is actually
    matched and a reply is returned In the HandlerResult, the 'done' flag will
    also be set.
    """

    def __call__(self, reply):
        if ok_send := self.accept(reply):
            return HandlerResult(send=ok_send, done=True)


class JoinChannel(WaitSendOnceHandler):
    """
    A WaitSendOnceHandler that joins a channel after after the server has had a
    chance to say welcome or set MODE lines.
    """

    def __init__(self, channel):
        self.join_msg = JOIN(channel)

    def accept(self, reply):
        # this is hardly 100% ... not all servers are going to follow this convention
        # but most seem to send a 001 Welcome message
        if reply.command.name == "001":
            return self.join_msg

        # If the 001 greeting trick fails, most seem to immediately
        # set some server MODEs right after pass/nick/user registration
        if reply.command.name == "MODE":
            return self.join_msg


class PingPong(ReplyHandler):
    def accept(self, reply):
        if reply.command.name == "PING":
            return PONG(*reply.params[0:])


class RawLog(RawHandler):
    """
    log messages to a file

    Takes either a filename (which it attempts to open in line buffered append
    mode) or a file handle as the first argument.

    RawLog will skip any messages that evauate as false.

    Optionally provide a process_cb that preprocesses messages. This can be
    used to add time signatures or skip messages:

        RawLog('/tmp/blah',
            process_cb=lambda x: datetime.datetime.now().ctime() + x)
            # process_cb can skip lines by returning something false

    Generally speaking, text based network protocols are meant to have a CRLF
    line ending (that's carriage return 0x0d line feed 0x0a). However, modern
    server operating systems (*nix and the like) normally prefer a
    line-feed-only ending, particularly in their log files.

    Set your preference for line endings in the 'line_ending' argument. The default
    is indeed '\x0a' per the above assumption.

        handler = RawLog(filename, line_ending='\x0a')

    The mode for the open() call can be set via the 'mode' argument. The default is 'a'.
    """

    fh = None

    def __init__(self, logfile, process_cb=None, line_ending="\x0a", mode="a"):
        self.process_cb = process_cb
        self.line_ending = line_ending
        if hasattr(logfile, "fileno") and hasattr(logfile, "write"):
            self.fh = logfile
        if self.fh is None:
            os.makedirs(os.path.dirname(logfile), exist_ok=True)
            self.fh = open(logfile, mode)

    def __del__(self):
        if self.fh is not None:
            try:
                self.fh.close()
                self.fh = None
            except AttributeError:
                pass

    def format_message(self, message):
        return str(message).rstrip(WS) + self.line_ending

    def __call__(self, message):
        # NOTE: open(name,'a') defaults to line buffering so there's no reason
        # to flush the write or anything like that. Note also that write()
        # blocks, which does halt the asyncio event loop. Probably the
        # buffering will normally hide this fact, but a later todo item might
        # be to use an asyncio based file writer.
        #
        # OTOH, if your disk is slow enough for this to ever matter, we'll
        # probably just run out of memory while queueing all those write tasks.

        message = self.format_message(message)

        if callable(self.process_cb):
            message = self.process_cb(message)
        if message:
            self.fh.write(message)


class SendRawLog(SendRawHandler):
    """
    Intended to be paired with a RawLog handler.

    rl = RawLog('filename')
    srl = SendRawLog(rl)

    loop.handlers.append(rl)
    loop.handlers.append(srl)

    """

    def __init__(self, rawlog_handler):
        if not isinstance(rawlog_handler, RawLog):
            raise TypeError(
                "SendRawLog is meant to be paired with a RawLog. Pass one as the only argument."
            )
        self.rlh = rawlog_handler

    def __call__(self, message):
        self.rlh(f"#SEND# {message}")
