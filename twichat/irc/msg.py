#!/usr/bin/env python
# coding: utf-8

"""
These outgoing message objects (based around twichat.irc.msg.Message) are just
message factories with some minor conveniences built in. For the parsed reply
message classes and gadgets, look in twichat.irc.reply instead.
"""

from .annoying import no_space_or_error

class Message:
    """
    The base Message factory is really just a simple concatenation tool that
    checks for a couple basic traps (e.g., only the last param after the
    command can have spaces in it, and that param must then start with a ':'
    charactor).

    The various subclasses in this module just try to add more convenience.
    They're fairly optional as is this Message class itself.

    n0 = NICK("namehere") # please change my name to "namehere"
    n1 = Message('nick', 'namehere') # same thing

    assert str(n0) == 'NICK namehere'
    assert str(n1) == 'NICK namehere'

    t0 = TargetMessage('#channelname', 'this is my silly message')
    t1 = Message('PRIVMSG', '#channelname', 'this is my silly message')

    assert str(t0) == 'PRIVMSG #channelname :this is my silly message'
    assert str(t1) == 'PRIVMSG #channelname :this is my silly message'
    """
    def __init__(self, cmd, *msg, **kw):
        self.msg = (cmd.upper(),)
        self.tags = kw

        if msg:
            last = msg[-1]
            msg = msg[:-1]

            for m in msg:
                no_space_or_error(m)

            # Space is allowed on the trailing arg, that's what
            # the ':' marker is for.
            #
            # There's a small amount of ambiguity though.
            #
            # While 'JOIN :#channel' probably works on most
            # servers, and is perfectly valid by rfc1459, some
            # servers just aren't going to handle that well.
            #
            # Also, some servers are going to expect to see ':'
            # on the trailing argument for some commands
            # regardless of whether it needs to be there or not
            # (eg, there's a space).
            #
            # So we do this annoying trick where if there's more
            # than one arg or if there's a space in the last arg,
            # then we use a ':'; otherwise we do not.
            #
            # That's probably not 100% correct, but it's likely
            # to work most of the time. The other alternative is
            # to not generalize at all. Perhaps that's better.

            if msg or " " in last:
                last = ":" + last

            self.msg += msg + (last,)

        if self.tags:
            pfx = '@' + ';'.join('='.join(item) for item in sorted(self.tags.items()))
            no_space_or_error(pfx)
            self.msg = (pfx,) + self.msg

    def __repr__(self):
        return " ".join(self.msg)


class USER(Message):
    def __init__(
        self,
        username,
        realname="Mr. Incognito",
        hostname="localhost",
        servername="unknown",
    ):
        """
        USER blah blah blah blah

        This is part of the normal IRC registration process.  In the olden days
        you'd PASS (iff necessary), NICK, then USER to register.  After this,
        the server would greet you warmly.

        Twitch servers don't seem to support the USER command, which would
        confuse probably every single IRC API out there; except that they seem
        to simply ignore the message if sent.
        """
        super().__init__("USER", username, hostname, servername, realname)


class TargetMessage(Message):
    def __init__(self, target, msg):
        super().__init__("PRIVMSG", target, msg)


class OneArgMessage(Message):
    def __init__(self, arg):
        super().__init__(self.__class__.__name__, arg)


class JOIN(OneArgMessage):
    def __init__(self, channel):
        """
        channel will automatically be prefixed with '#' unless '&' or '#' is
        given at the start of the name

            str(JoinMessage('channelname')) → "JOIN #channelname"

        Note that there are two types of IRC channels:
          '#' a distributed channel known to the whole network
          '&' a server channel known by only that server, and only joinable
              by users on that server

        Also note that some channels really do have multiple '#' prefixes...
        In which case, it must actually be expressed twice, since the automatic
        prefixing will be skipped without this:

            str(JoinMessage('math')) → "JOIN #math"
            str(JoinMessage('#math')) → "JOIN #math"
            str(JoinMessage('##math')) → "JOIN ##math"

        Interestingly, if you join '#math' on freenode, you'll actually be
        joined to '##math'; which is somewhat inexplicable. IRC! \\o/
        """

        if not channel.startswith("#"):
            if not channel.startswith("&"):
                channel = "#" + channel

        super().__init__(channel)


class PASS(OneArgMessage):
    pass


class NICK(OneArgMessage):
    pass


class PING(OneArgMessage):
    """
    We set up our PING messages as a single argument affair. Technically there's a forwarding scheme in RFC 1459
    which means 'PING blah blah2' implies 'blah' should forward the PING to 'blah2'. We simply ignore this.

        PING("target-here")
    """


class PONG(Message):
    """
    Technically a PONG message should probably contain all the params from the PING it's replying to.

        PONG(*parsed_reply_obj.params[1:])
    """
