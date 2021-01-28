#!/usr/bin/env python
# coding: utf-8

import asyncio


class ExampleLoop:
    loop = None

    def __init__(self, things=5):
        self.things = things
        self.running = False
        self.tasks = list()

    async def thing(self, duration=1):
        ret = self.things
        name = f"thing({ret})"
        print(f"{name} starting")
        await asyncio.sleep(duration)
        self.things -= 1
        print(f"{name} fired")
        if self.things < 1:
            print(f"{name} telling mainloop to shutdown")
            self.running = False
        return ret

    async def other_thing(self, arg, triggers=((5, 7), (3, 1))):
        name = f"other_thing({arg})"
        for trigger, duration in triggers:
            if arg == trigger:
                print(f"{name} starting trigger={trigger} duration={duration}")
                await asyncio.sleep(duration)
                print(f"{name} fired")
            else:
                print(f"{name} NOP")

    async def check_on_pending_tasks(self):
        before = len(self.tasks)
        self.tasks = [task for task in self.tasks if not task.done()]
        after = len(self.tasks)
        if 0 < after < before:
            print(f"{before-after} async task(s) finished")

    async def main(self):
        print("running")
        while self.running:
            res = await self.thing()
            task = self.loop.create_task(self.other_thing(res))
            self.tasks.append(task)
            await self.check_on_pending_tasks()
        if self.tasks:
            print("final cleanup")
            await asyncio.gather(*self.tasks)
        print("fin")

    def start(self):
        self.running = True
        print("start() creating event loop")
        self.loop = asyncio.get_event_loop()
        print("start() running main() until complete")
        self.loop.run_until_complete(self.main())
        print("start() closing loop")
        self.loop.close()


if __name__ == "__main__":
    el = ExampleLoop()
    el.start()
