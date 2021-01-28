#!/usr/bin/env python
# coding: utf-8
# pylint: disable=no-value-for-parameter
# (click commands make function signatures really weird)

import logging
import click

from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from twichat import TWILoop
from twichat.handlers import JoinChannel, RawLog, PingPong, SendRawLog
from twichat.irc.msg import TargetMessage
from twichat.handlers import ReplyHandler
from twichat.const import UUID

log = logging.getLogger(__name__)

class PrintAll(ReplyHandler):
    def accept(self, reply):
        print(reply)


async def interactive_shell(channel, send_msg_f, stop_loop_f):
    if not channel.startswith("#"):
        channel = "#" + channel
    session = PromptSession("> ")
    try:
        while True:
            with patch_stdout():
                result = await session.prompt_async()
            result = result.rstrip()
            cmd_level = 0
            while result.startswith("/"):
                result = result[1:]
                cmd_level += 1
            if not result:
                continue
            if cmd_level >= 1:
                if cmd_level >= 2:
                    send_msg_f(result)
                else:
                    cmd, *parts = result.split()
                    if cmd not in ("msg", "help", "quit",):
                        print(f"ERROR: /{cmd} unknown")
                        cmd = "help"
                    if cmd == "help":
                        print("/msg :- send a message: eg: /msg target words here")
                        print("/quit :- quit")
                        print("/help :- print this help")
                        print("\n//RAW command here :sent just like this")
                    elif cmd == "quit":
                        break
                    elif cmd == "msg":
                        if len(parts) < 2:
                            print("ERROR: /msg <target> <message>")
                        else:
                            send_msg_f(TargetMessage(parts[0], " ".join(parts[1:])))
            else:
                send_msg_f(TargetMessage(channel, result))
    except (EOFError, KeyboardInterrupt):
        print("\nOK, see ya")
    stop_loop_f()


@click.command()
@click.option("--host", type=str, default="irc.freenode.net")
@click.option("--port", type=int, default=6697)
@click.option("--nick", type=str, default=f"tctc_{UUID}")
@click.option("--channel", type=str, default="twichat")
@click.option("-v", "--verbose", "verbosity", count=True)
@click.option(
    "passwd",
    "--pass",
    type=str,
    envvar="PASS",
    help="can also be passed via PASS= environment variable",
)
@click.option("--logfile", type=click.Path(dir_okay=False, writable=True))
def run(host, port, channel, nick, logfile, passwd, verbosity):
    if verbosity > 0:
        level = logging.INFO
        if verbosity > 1:
            level = logging.DEBUG
        log.info('turning on logging at level=%d', level)
        logging.basicConfig(
            level=level,
            datefmt="%Y-%m-%d %H:%M:%S",
            format="%(name)s [%(process)d] %(levelname)s: %(message)s",
        )
    loop = TWILoop(host=host, port=port, nick=nick, passwd=passwd)
    loop.handlers.append(JoinChannel(channel))
    loop.handlers.append(PingPong())
    loop.handlers.append(PrintAll())
    if logfile:
        log.info('logging RawLog() and SendRawLog() to %s', logfile)
        rlh = RawLog(logfile)
        srl = SendRawLog(rlh)
        loop.handlers.append(rlh)
        loop.handlers.append(srl)
    loop.start(interactive_shell(channel, loop.send, loop.stop))


if __name__ == "__main__":
    run()
