#!/usr/bin/env python
# coding: utf-8
# pylint: disable=no-self-use

from collections import namedtuple
from lark import Lark, Transformer, UnexpectedToken

Origin = namedtuple("Origin", ["name", "user", "host"])
User = namedtuple("User", ["name"])
Host = namedtuple("Host", ["name"])
Command = namedtuple("Command", ["name"])
TagPair = namedtuple("TagPair", ['name', 'value'])

ParsedReply = namedtuple("Reply", ['tags', "origin", "command", "params"])

MUT_MARK = "←!"

class TagSet(dict):
    pass

class Params(list):
    pass

class MarkedUnexpectedToken(ValueError):
    def __init__(self, untoken, line):
        marked = line[: untoken.column] + MUT_MARK + line[untoken.column :]
        super().__init__(f'failed to parse "{marked}" at the "{MUT_MARK}" mark')


class ReplyTransformer(Transformer):
    def trailing(self, v):
        if v[0].type[0] == "T":
            return v[0].value[1:]
        return v[0].value

    def middle(self, v):
        return v[0].value

    def command(self, v):
        return Command(v[0].value)

    def params(self, v):
        return Params(v[1:])

    def server_or_nick(self, v):
        return v[0].value

    def username(self, v):
        return User(v[1].value)

    def hostname(self, v):
        return Host(v[1].value)

    def tagstr(self, v):
        return v[0].value

    def tagpair(self, v):
        # eg ('badge-info', Token(EQ))
        if len(v) == 2:
            return TagPair(v[0],None)

        # eg ('badges', Token(EQ), 'staff/1,bits/1000')
        if len(v) == 3:
            return TagPair(v[0],v[2])

        # hopefully there's no more variations to consider
        raise ValueError(f"WTF(v={v})")

    def id3tags(self, v):
        # v[0] is Token(@)
        # v[1] (if there is one) is tagpair 2-tuple
        # v[2] (if there is one) is Token(;)
        # v[3] would be a tagpair 2-tuple again
        return TagSet(x for x in v if isinstance(x, TagPair))

    def prefix(self, v):
        name, *other = v[1:-1]
        kw = dict(name=name, user=None, host=None)
        for item in other:
            if isinstance(item, User):
                kw["user"] = item
            elif isinstance(item, Host):
                kw["host"] = item
        return Origin(**kw)

    def reply(self, v):
        kw = dict(tags=None, origin=None, command=None, params=None)
        for i in v:
            if isinstance(i, Origin):
                kw["origin"] = i
            elif isinstance(i, Command):
                kw["command"] = i
            elif isinstance(i, Params):
                kw["params"] = i
            elif isinstance(i, TagSet):
                kw["tags"] = i
        return ParsedReply(**kw)


__REPLY_PARSER = None


def ReplyParser():
    global __REPLY_PARSER

    if __REPLY_PARSER is not None:
        return __REPLY_PARSER

    # CSTRING :- command names are fairly restrictive... just word chars
    # MSTRING :- middle params have these exact restrictions apparently
    # TSTRING :- the last param must be prefixed with a colon and then anything goes after that
    # NSTRING :- names can be almost anything, probably, and RFC1459 is ambiguous about it
    #            I've chosen to allow almost anything except the symbols the
    #            parser uses to separate origin fields; ... and I disallowed
    #            spaces, but I think those are technically allowed in channel
    #            names and other things. You just won't see it come up often
    #            enough to fret about it in here just yet.

    __REPLY_PARSER = Lark(
        r"""
        ?start: reply
        reply: id3tags? prefix? command params?
        params: SP middle* trailing
        id3tags: AT tagpair (SEMI tagpair)* SP
        tagpair: tagstr EQ tagstr | tagstr EQ
        tagstr: PSTRING
        middle: MSTRING SP?
        trailing: TSTRING | MSTRING
        command: (CSTRING | DIGITS)
        prefix: COLON server_or_nick username? hostname? SP
        server_or_nick: NSTRING
        username: BANG NSTRING
        hostname: AT NSTRING
        DIGITS: /\d+/
        CSTRING: /\w[\w\d]+/
        NSTRING: /[^\x00\x0d\x0a@:!\s]+/
        TSTRING: ":" /.*/
        MSTRING: /[^:\x00\x0d\x0a\s]+/
        PSTRING: /[^=:;\s\x00\x0d\x0a]+/
        AT: "@"
        EQ: "="
        COLON: ":"
        SEMI: ";"
        BANG: "!"
        SP: /\s+/
        """,
        parser="lalr",
        transformer=ReplyTransformer(),
    )

    return __REPLY_PARSER


def parse(line):
    try:
        return ReplyParser().parse(line)
    except UnexpectedToken as ut:
        raise MarkedUnexpectedToken(ut, line) from ut
