#!/usr/bin/env python
# coding: utf-8

import pytest
from t.lib import TEST_LINES, generate_reply_names


@pytest.fixture(params=TEST_LINES)
def a_reply(request):
    return request.param


def _generate_numbered_fixtures():
    g = globals()
    for name, value in generate_reply_names():

        def lexical_bind(n, v):
            def _f():
                yield v

            _f.__name__ = n
            return pytest.fixture(_f)

        g[name] = lexical_bind(name, value)


_generate_numbered_fixtures()
