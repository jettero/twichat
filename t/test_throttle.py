#!/usr/bin/env python
# coding: utf-8

from time import time as now
import pytest
from twichat.throttle import Throttle, OverThrottle

NOW = now()


def test_memory_throttle(mocker):
    fake_time = NOW

    def ftime():
        return fake_time

    mocker.patch("time.time", ftime)

    t0 = Throttle("main", items_per_interval=3, interval_in_seconds=5)
    assert t0.count == 0
    assert len(t0.ticks) == 0

    t0.tick()
    assert t0.count == 1
    assert len(t0.ticks) == 1

    t0.tick()  # dt=0
    assert t0.count == 2
    assert len(t0.ticks) == 1

    fake_time = NOW + 1

    t0.tick()  # dt=1
    assert t0.count == 3
    assert len(t0.ticks) == 2

    with pytest.raises(OverThrottle):
        t0.tick()

    for dt in range(2, 5):
        # dt really runs through 2-4
        fake_time = NOW + dt

        assert t0.count == 3
        assert len(t0.ticks) == 2

    fake_time = NOW + 5

    assert t0.count == 1
    assert len(t0.ticks) == 1

    fake_time = NOW + 6

    assert t0.count == 0
    assert len(t0.ticks) == 0
