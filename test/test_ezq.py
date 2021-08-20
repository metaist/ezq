#!/usr/bin/env python
# coding: utf-8
"""Test ezq functions."""

# native
from functools import partial
import time

# pkg
import ezq


def msg_counter(q: ezq.Queue, n_msg: int, num: int = 0):
    """Count up the number of messages.

    Args:
        q (ezq.Queue): queue to read from
        n_msg (int): expected number of messages
        num (int, optional): process number. Defaults to 0.
    """
    assert num <= ezq.NUM_CPUS, "expect subprocess number to be less than cpus"

    count = sum(msg.data for msg in ezq.iter_msg(q))
    assert count == n_msg, f"expect {n_msg} messages"


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


def test_all_msg():
    """Expect iterator to iterate over the queue."""
    num = 1000
    q = ezq.Queue()
    for _ in range(num):
        q.put(ezq.Msg("MSG", 1))
    q.put(ezq.END_MSG)

    total = 0
    for msg in ezq.iter_msg(q):
        total += msg.data
    assert total == num, "expect iterator to get all messages"


def test_end_early():
    """Expect iterator to end early."""
    num = 1000
    num_stop = 900  # give the queue time to warm up
    q = ezq.Queue()
    for _ in range(num):
        q.put(ezq.Msg("MSG", 1))
    q.put(ezq.END_MSG)

    total = 0
    for msg in ezq.iter_msg(q):
        total += msg.data
        if total == num_stop:
            ezq.stop_iter_msg()
    assert total == num_stop, "expect iterator to stop early"


def test_single():
    """Test single subprocess."""
    n_msg = 1000
    n_sum = sum(range(n_msg))

    q = ezq.Queue()
    workers = ezq.start(partial(msg_summer, q, n_msg, n_sum), 1)

    for i in range(n_msg):
        q.put(ezq.Msg(data=i))

    ezq.wait(q, workers)
    time.sleep(0.1)  # give it time to finish


def test_numbered():
    """Test numbered processes."""
    n_msg = 1000
    q = ezq.Queue()
    workers = ezq.start_numbered(partial(msg_counter, q))

    for _ in range(n_msg):
        q.put(ezq.Msg(data=1))

    ezq.wait(q, workers)
    time.sleep(0.1)  # give it time to finish
