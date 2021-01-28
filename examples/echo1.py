#!/usr/bin/env python
# coding: utf-8
# pylint: disable=no-value-for-parameter
# (click commands make function signatures really weird)

import click

from twichat import TWILoop
from twichat.handlers import JoinChannel, ReplyHandler, PingPong
from twichat.irc.reply import DirectMessage
from twichat.irc.msg import TargetMessage
from twichat.const import UUID


class EchoDM(ReplyHandler):
    def accept(self, reply):

        print(reply)  # show something on console

        if isinstance(reply, DirectMessage):
            return TargetMessage(reply.sender, f"echo: {reply.msg}")


@click.command()
@click.option("--host", type=str, default="irc.freenode.net")
@click.option("--port", type=int, default=6697)
@click.option("--nick", type=str, default=f"tcecho1_{UUID}")
@click.option(
    "passwd",
    "--pass",
    type=str,
    envvar="PASS",
    help="can also be passed via PASS= environment variable",
)
@click.option("--channel", type=str, default="twichat")
def run(host, port, channel, nick, passwd):
    loop = TWILoop(host=host, port=port, nick=nick, passwd=passwd)
    loop.handlers.append(JoinChannel(channel))
    loop.handlers.append(PingPong())
    loop.handlers.append(EchoDM())
    loop.start()


if __name__ == "__main__":
    run()
