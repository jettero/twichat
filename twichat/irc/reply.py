#!/usr/bin/env python
# coding: utf-8
# pylint: disable=attribute-defined-outside-init

import re
import datetime
from abc import abstractmethod, ABC
from .parser import ParsedReply, parse as parse_reply_text


class GrokError(TypeError):
    def __init__(self, reply):
        super().__init__(f"unable to deal with {reply}, expected type {ParsedReply}")


def grok(reply):
    return Reply.grok(reply)


parse = grok


class _RE:
    chan = re.compile(r"^[&#]")
    numb = re.compile(r"^\d+$")
    mode = re.compile(r"^:?(?P<addsub>[+-])(?P<modes>\w)")


def ischannel(name):
    return bool(_RE.chan.search(name))


def isnumber(name):
    return bool(_RE.numb.match(name))


class Reply(ABC, ParsedReply):
    _msg = _target = None
    cname = lcname = None
    reply_classes = list()

    @classmethod
    def grok(cls, reply):
        if isinstance(reply, str):
            reply = parse_reply_text(reply)
        if not isinstance(reply, ParsedReply):
            raise GrokError(reply)
        reply = cls(*reply)
        for crc_cls in reversed(cls.reply_classes):
            if crc_cls.accept(reply):
                return crc_cls.wrap(reply)
        return reply

    parse = grok

    @classmethod
    @abstractmethod
    def accept(cls, reply):
        raise NotImplementedError("post_wrap missing")

    @abstractmethod
    def post_wrap(self):
        raise NotImplementedError("post_wrap missing")

    def __init_subclass__(cls):
        cls.reply_classes.append(cls)

    @classmethod
    def wrap(cls, reply):
        if not isinstance(reply, ParsedReply):
            raise GrokError(reply)
        obj = cls(*reply)
        obj.post_wrap()
        obj.cname = cls.__name__
        obj.lcname = obj.cname.lower()
        return obj

    @property
    def source(self):
        if self.origin:
            if self.origin.name:
                return self.origin.name
            if self.origin.user:
                if self.origin.host:
                    return f"{self.origin.user}@{self.origin.host}"
                return f"{self.origin.user}"
        return "unknown"

    @property
    def target(self):
        # not always true or useful; usually the first param is the target
        if self._target:
            return self._target
        if self.params:
            self._target = self.params[0]
        return self._target

    @target.setter
    def target(self, v):
        self._target = v

    @property
    def msg(self):
        if self._msg is not None:
            return self._msg
        if len(self.params) > 1:
            self._msg = " ".join(self.params[1:])
        return self._msg

    @msg.setter
    def msg(self, v):
        self._msg = v

    def stringify(self):
        p = " ".join(self.params)
        return f"{self.source} {self.command.name} {p}"

    def __repr__(self):
        s = self.stringify()
        if s:
            return f"{self.cname}<{s}>"
        return self.cname


class Arrive(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name == "JOIN":
            return True

    def post_wrap(self):
        self.joiner = self.source
        self.channel = self.target

    def stringify(self):
        return f"{self.joiner} arrived in {self.channel}"


class Depart(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name == "PART" or reply.command.name == "QUIT":
            return True

    def post_wrap(self):
        self.leaver = self.source
        self.channel = self.target

    def stringify(self):
        return f"{self.leaver} has left {self.channel}"


class DirectMessage(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name == "PRIVMSG" and not ischannel(reply.target):
            return True

    def post_wrap(self):
        self.sender = self.source
        self.receiver = self.target

    def stringify(self):
        return f'{self.sender} says, "{self.msg}" to {self.receiver}'


class ChannelMessage(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name == "PRIVMSG" and ischannel(reply.target):
            return True

    def post_wrap(self):
        self.sender = self.source
        self.channel = self.target

    def stringify(self):
        return f'{self.sender} says, "{self.msg}" on {self.channel}'


class ServerNotification(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name == "NOTICE" or isnumber(reply.command.name):
            return True

    def post_wrap(self):
        pass

    def stringify(self):
        return f"{self.source} notifies: {self.msg}"


class Mode(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name == "MODE":
            return True

    def post_wrap(self):
        self.add = set()
        self.sub = set()

        m = _RE.mode.match(self.msg)
        if m:
            addsub, modes = m.groups()
            if addsub == "+":
                self.add = set(x for x in modes)
            elif addsub == "-":
                self.sub = set(x for x in modes)
            else:
                raise ValueError(
                    f"not really sure how to deal with MODE<{self.msg}> on {self.target}"
                )

    def stringify(self):
        if self.add:
            jm = "".join(self.add)
            return f"{self.source} set +{jm} on {self.target}"
        if self.sub:
            jm = "".join(self.sub)
            return f"{self.source} set -{jm} on {self.target}"
        return f"{self.source} did some unknown mode thing to {self.target}"


class PING(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name == "PING":
            return True

    def post_wrap(self):
        pass

    def stringify(self):
        return ", ".join(self.params[0:])


class PONG(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name == "PONG":
            return True

    def post_wrap(self):
        pass

    def stringify(self):
        return ", ".join(self.params[0:])


class TOPIC(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name == "TOPIC":
            return True

    def post_wrap(self):
        self.topic = self.msg
        self.channel = self.target
        self.changer = self.source

    def stringify(self):
        return f'{self.changer} set {self.channel} topic, "{self.topic}"'


class TopicNotice(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name == "332":
            return True

    def post_wrap(self):
        self.msg = self.topic = self.params[2]
        self.channel = self.params[1]

    def stringify(self):
        return f'{self.channel} topic is, "{self.topic}"'


class TopicAuthor(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name in "333":
            return True

    def post_wrap(self):
        self.channel = self.params[1]
        self.author = self.params[2]
        self.nick = self.author.split("!")[0]
        self.mtime = self.params[3]
        if isnumber(self.mtime):
            try:
                ctime = datetime.datetime.utcfromtimestamp(int(self.mtime)).ctime()
                self.mtime = ctime
            except:
                self.mtime = f"timestamp={self.mtime}"

    def stringify(self):
        return f"{self.channel} topic set by {self.nick}, {self.mtime}"


class NameList(Reply):
    class Nick:
        def __init__(self, nick, op=False):
            self.nick = nick
            self.op = op

        def __repr__(self):
            if self.op:
                return f"@{self.nick}"
            return self.nick

    @classmethod
    def accept(cls, reply):
        if reply.command.name == "353":
            return True

    def post_wrap(self):
        # in a 353 REPL_NAMREPLY message
        #   :palmereldritch3s.tmi.twitch.tv 353 palmereldritch3s = #palmereldritch3s :palmereldritch3s
        #   :tepper.freenode.net 353 just_testing_som @ #twichat :just_testing_som jettero

        self.channel = self.params[2]

        self.nicks = list()
        for name in self.params[3].split(" "):
            if name.startswith("@"):
                self.nicks.append(self.Nick(name[1:], op=True))
            else:
                self.nicks.append(self.Nick(name))

    def stringify(self):
        sp = ", ".join(str(x) for x in self.nicks)
        return f"present: {sp}"


class EndNameList(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name == "366":
            return True

    def post_wrap(self):
        self.channel = self.params[1]

    def stringify(self):
        pass


class ChannelURL(Reply):
    @classmethod
    def accept(cls, reply):
        if reply.command.name == "328":
            return True

    def post_wrap(self):
        self.channel = self.params[1]
        self.url = self.params[2]

    def stringify(self):
        return f"{self.channel} URL: {self.url}"
