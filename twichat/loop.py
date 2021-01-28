#!/usr/bin/env python
# coding: utf-8

import signal
import asyncio
import logging
from .irc.reply import grok
from .irc.conn import IRCConnection
from .const import (
    TWITCH_HOST as TH,
    TWITCH_PORT as TP,
    INSTALL_DIR,
    PYTHON_DIR,
)
from .handlers import HandlerResult, ReplyHandler, RawHandler, SendRawHandler

log = logging.getLogger(__name__)


class RegistrationInfo(dict):
    def __bool__(self):
        return bool(self.get("nick"))

    def __repr__(self):
        pretend = dict(**self)
        if pretend.get("passwd"):
            pretend["passwd"] = "xxxx"
        return repr(pretend)


class TWILoop:
    main_coro = loop = sock = None

    def __init__(
        self,
        host=TH,
        port=TP,
        use_ssl=True,
        verify_ssl=True,
        nick=None,
        passwd=None,
        username=None,
        realname="M. Incognito",
        hostname=None,
    ):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl

        self.handlers = list()
        self.running = False
        self.tasks = list()

        self.registration_info = RegistrationInfo(
            nick=nick,
            passwd=passwd,
            username=username,
            realname=realname,
            hostname=hostname,
        )

    def start(self, *other_jobs):
        log.debug("start() starting asyncio.event_loop")
        self.running = True
        if other_jobs:
            self.main_coro = asyncio.gather(*((self.main(),) + other_jobs))
        else:
            self.main_coro = self.main()
        loop = asyncio.get_event_loop()
        # once we set this task factory, any new task we create
        # is automatically tracked in self.tasks
        loop.set_task_factory(self.task_factory)
        log.debug("start() building connection")
        self.sock = IRCConnection(
            host=self.host,
            port=self.port,
            use_ssl=self.use_ssl,
            verify_ssl=self.verify_ssl,
        )
        log.debug("start() adding signal handlers")
        loop.add_signal_handler(signal.SIGINT, self.signal_handler, signal.SIGINT)
        loop.add_signal_handler(signal.SIGTERM, self.signal_handler, signal.SIGTERM)
        loop.add_signal_handler(signal.SIGQUIT, self.signal_handler, signal.SIGQUIT)
        try:
            loop.run_until_complete(self.main_coro)
        except asyncio.exceptions.CancelledError:
            pass

    def signal_handler(self, signo):
        if signo == 2:
            print(" ")  # otherwise the screen looks like shit with a ^C on that line
        log.info("received signal=%d, issuing stop()")
        self.stop()

    def task_factory(self, loop, coro, name=None):
        if name is None:
            try:
                cobj = coro.cr_code
                fname = cobj.co_filename
                if fname.startswith(INSTALL_DIR):
                    fname = fname[len(INSTALL_DIR) + 1 :]
                if fname.startswith(PYTHON_DIR):
                    fname = fname[len(PYTHON_DIR) + 1 :]
                name = f"{fname}.{cobj.co_firstlineno}:{cobj.co_name}"
            except Exception as e:
                log.debug("failed to build a name for coro: %s", e)
        task = asyncio.tasks.Task(coro, loop=loop, name=name)
        if coro is not self.main_coro:
            self.tasks.append(task)
        return task

    def stop(self):
        self.running = False
        if self.sock is not None and not self.sock.closed:
            self.sock.close()

    def send(self, message):
        log.debug("send() invoking SendRawHandler(message=%s)", message)
        if self.iter_handlers(message, filter_cls=SendRawHandler):
            log.debug("send() a handler says we should abort sending: %s", message)
            return
        self.sock.writeline(message)

    async def readline(self):
        return await self.sock.readline()

    def iter_handlers(self, handle_me, filter_cls=ReplyHandler):
        log.debug('iter_handlers() iterating about %s using %s', handle_me, filter_cls)
        stop_handles = False
        to_remove = list()
        for handler in self.handlers:
            log.debug('iter_handlers() considering handler=%s', handler)
            if isinstance(handler, filter_cls):
                try:
                    res = handler(handle_me)
                except Exception as error1:
                    try:
                        log.error(
                            "iter_handlers() error handling handle_me=%s with handler=%s: %s",
                            handle_me,
                            handler,
                            error1,
                        )
                    except Exception as error2:
                        log.error(
                            'iter_handlers() error logging error="%s": %s',
                            error1,
                            error2,
                            exc_info=True,
                        )
                    continue
                if isinstance(res, HandlerResult):
                    if res.send:
                        log.debug('iter_handlers() handler has something to say')
                        if isinstance(res.send, (list, tuple)):
                            for item in res.send:
                                self.send(item)
                        else:
                            self.send(res.send)
                    if res.done:
                        log.debug('iter_handlers() handler says it fulfilled its purpose')
                        to_remove.append(handler)
                    if res.stop_handles:
                        log.debug('iter_handlers() handler says it handled the message')
                        stop_handles = True
                        break
                    if res.stop_mainloop:
                        log.debug('iter_handlers() handler says this whole circus is done')
                        self.stop()
                elif res is not None:
                    log.debug("ignoring result=%s from handler=%s", res, handler)
        for handler in to_remove:
            self.handlers.remove(handler)
        # We return stop_handles so multi-stage functions can abort
        # see `if self.iter_handlers(...RawHandler...)` below
        return stop_handles

    async def handle_message(self, message):
        if self.registration_info:
            log.debug(
                "handle_message() sending registration info %s", self.registration_info
            )
            # we don't know how long it takes to send, and this loop is async,
            # so we prevent accidentally re-sending by deleting the reginfo
            # before sending.
            ri = self.registration_info
            self.registration_info = False
            self.sock.register(**ri)
        log.debug("handle_message() invoking RawHandler(message=%s)", message)
        if self.iter_handlers(message, filter_cls=RawHandler) is True:
            log.debug('handle_message() RawHandler "handled" message')
            return
        reply = grok(message)
        log.debug("handle_message() invoking ReplyHandler(reply=%s)", reply)
        self.iter_handlers(reply)

    async def main(self):
        log.debug("main() starting up by starting socket")
        await self.sock.start()
        log.debug("main() entering mainloop")
        while self.running:
            line = await self.readline()  # NOTE: conn.readline issues rstrip()
            if not line:
                log.debug("main() line was false, stopping socket")
                self.stop()
                break
            await self.handle_message(line)
            await self.check_on_pending_tasks()
        log.debug("main() seems like we're done here")
        if self.tasks:
            log.debug("main() just waiting for the last few tasks to finish")
            await asyncio.gather(*self.tasks)
        log.debug("FIN")

    async def check_on_pending_tasks(self):
        self.tasks = [task for task in self.tasks if not task.done()]
        for task in self.tasks:
            log.debug("check_on_pending_tasks() task=%s", task.get_name())


def twitch(*a, **kw):
    return TWILoop(*a, **kw)


# this is mainly just for testing purposes
def freenode(*a, **kw):
    return TWILoop(*a, host="irc.freenode.net", port=6697, **kw)
