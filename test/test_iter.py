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

    assert q.qsize() == num, "expect all messages queued"

    total = sum(msg.data for msg in q.items())
    assert num == total, "expect iterator to get all messages"


def test_sortiter_sorted_list() -> None:
    """Sort a list of sorted numbers."""
    num = 1000
    order = list(range(num))
    want = order.copy()
    have = list(ezq.sortiter(order, key=ident))
    assert want == have, "expected numbers in order"


def test_sortiter_random_list() -> None:
    """Sort a list of numbers."""
    num = 1000
    order = list(range(num))
    want = order.copy()
    random.shuffle(order)

    have = list(ezq.sortiter(order, key=ident))
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
