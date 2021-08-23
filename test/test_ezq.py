#!/usr/bin/env python
# coding: utf-8
"""Test ezq functions."""

# native
import random

# pkg
import ezq

# iterating over queue #

identity = lambda x: x
"""Returns the given argument."""


def test_iter_q():
    """Iterate over all messages."""
    num = 1000
    q = ezq.Queue()
    for _ in range(num):
        ezq.put_msg(q, "MSG", 1)

    total = sum(msg.data for msg in ezq.iter_q(q))
    assert num == total, "expect iterator to get all messages"


def test_sortiter_sorted_list():
    """Sort a list of sorted numbers."""
    num = 1000
    order = list(range(num))
    want = order.copy()
    got = list(ezq.sortiter(order, key=identity))
    assert want == got, "expected numbers in order"


def test_sortiter_random_list():
    """Sort a list of numbers."""
    num = 1000
    order = list(range(num))
    want = order.copy()
    random.shuffle(order)

    got = list(ezq.sortiter(order, key=identity))
    assert want == got, "expected numbers in order"


def test_sortiter_messages():
    """Sort messages in order."""
    num = 1000
    order = list(range(num))
    want = order.copy()
    random.shuffle(order)

    q = ezq.Queue()
    for o in order:
        ezq.put_msg(q, order=o)

    got = [msg.order for msg in ezq.sortiter(ezq.iter_q(q))]
    assert want == got, "expected ids in order"


def test_sortiter_gap():
    """Sort messages in order even if there's a gap."""
    num = 1000
    order = list(range(num - 10)) + list(range(num - 5, num))
    want = order.copy()
    random.shuffle(order)

    q = ezq.Queue()
    for o in order:
        ezq.put_msg(q, order=o)

    got = [msg.order for msg in ezq.sortiter(ezq.iter_q(q))]
    assert want == got, "expected ids in order"


# running subprocesses #


def msg_summer(q: ezq.Queue, n_msg: int, n_sum: int):
    """Add up the message content.

    Args:
        q (ezq.Queue): queue to read from
        n_msg (int): expected number of messages
        n_sum (int): expected sum of message data
    """

    result, count = 0, 0
    for msg in ezq.iter_msg(q):
        result += msg.data
        count += 1
    assert count == n_msg, f"expect {n_msg} messages"
    assert result == n_sum, f"expect sum of {n_sum}"


def msg_counter(in_q: ezq.Queue, out_q: ezq.Queue, num: int):
    """Count the number of messages.

    Args:
        in_q (ezq.Queue): queue to read from
        out_q (ezq.Queue): queue to report count
        num (int): process number
    """
    assert num <= ezq.NUM_CPUS, "expect subprocess number to be less than cpus"

    count = sum(msg.data for msg in ezq.iter_msg(in_q))
    out_q.put(ezq.Msg(data=count))


def test_run_one():
    """Single subprocess with fixed arguments."""
    n_msg = 1000
    n_sum = sum(range(n_msg))

    q = ezq.Queue()
    worker = ezq.run(msg_summer, q, n_msg=n_msg, n_sum=n_sum)

    for i in range(n_msg):
        ezq.put_msg(q, data=i)

    ezq.endq_and_wait(q, worker)


def test_run_many():
    """Run several subprocesses with different arguments."""
    n_msg = 1000
    in_q = ezq.Queue()
    out_q = ezq.Queue()

    workers = [ezq.run(msg_counter, in_q, out_q, num=i) for i in range(ezq.NUM_CPUS)]

    for _ in range(n_msg):
        ezq.put_msg(in_q, data=1)
    ezq.endq_and_wait(in_q, workers)  # workers done

    count = sum(msg.data for msg in ezq.iter_q(out_q))
    assert count == n_msg, f"expect {n_msg} messages"
