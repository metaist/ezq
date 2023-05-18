#!/usr/bin/env python
# coding: utf-8
"""Test iteration helpers."""

# native
import random

# pkg
import ezq


def ident(x: int) -> int:
    """Return the number given."""
    return x


def test_iter_q() -> None:
    """Iterate over all messages."""
    num = 1000
    q = ezq.Q()

    for _ in range(num):
        q.put(1)

    if not ezq.IS_MACOS:
        assert q.qsize() == num, "expect all messages queued"

    total = sum(msg.data for msg in q.items())
    assert num == total, "expect iterator to get all messages"


def test_sortiter_sorted_list() -> None:
    """Sort a list of sorted numbers."""
    num = 1000
    want = list(range(num))

    q = ezq.Q()
    for num in range(num):
        q.put(order=num)

    have = [msg.order for msg in q.end().sorted()]
    assert want == have, "expected numbers in order"


def test_sortiter_random_list() -> None:
    """Sort a list of numbers."""
    num = 1000
    want = list(range(num))

    temp = want.copy()
    random.shuffle(temp)

    q = ezq.Q()
    for num in temp:
        q.put(order=num)  # sending things out of order

    have = [msg.order for msg in q.items(sort=True)]
    assert want == have, "expected numbers in order"


def test_sortiter_messages() -> None:
    """Sort messages in order."""
    num = 1000
    order = list(range(num))
    want = order.copy()
    random.shuffle(order)

    q = ezq.Q()
    for o in order:
        q.put(order=o)

    have = [msg.order for msg in q.end().sorted()]
    assert want == have, "expected ids in order"


def test_sortiter_gap() -> None:
    """Sort messages in order even if there's a gap."""
    num = 1000
    order = list(range(num - 10)) + list(range(num - 5, num))
    want = order.copy()
    random.shuffle(order)

    q = ezq.Q()
    for o in order:
        q.put(order=o)

    have = [msg.order for msg in q.end().sorted()]
    assert want == have, "expected ids in order"
