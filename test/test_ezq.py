#!/usr/bin/env python
# coding: utf-8
"""Test ezq functions."""

# native
import operator
from typing import Callable

# pkg
import ezq


def test_q_wrapper() -> None:
    """Use underlying queue."""
    q = ezq.Q("thread")
    q.put(1)
    q.put(ezq.Msg(data=2))

    if not ezq.IS_MACOS:
        assert q.qsize() == 2, "expected function to be delegated to queue"

    want = [1, 2]
    have = [msg.data for msg in q.items(cache=True)]
    assert have == want, "expected both to be the same"

    have = [msg.data for msg in q.items(cache=True)]
    assert have == want, "expected same results after .items() twice"


# example workers


def worker_sum(q: ezq.Q, out: ezq.Q, num: int) -> None:
    """Worker that sums message data.

    Args:
        in_q (ezq.Q): queue to read from
        out_q (ezq.Q): queue to report count
        num (int): worker number
    """
    result = sum(msg.data if isinstance(msg.data, int) else msg.data() for msg in q)
    out.put((num, result))


# running subprocesses and threads #


def test_run_processes() -> None:
    """Run several workers with different arguments."""
    n_msg = 1000

    q, out = ezq.Q(), ezq.Q()
    workers = [ezq.run(worker_sum, q, out, num=i) for i in range(ezq.NUM_CPUS)]

    def wrap_lambda(i: int) -> Callable[[], int]:
        """Wrap a number in a lambda so thread-context works."""
        return lambda: i

    for num in range(n_msg):
        q.put(wrap_lambda(num))

    # for num in range(n_msg):
    #     q.put(ezq.Msg(data=num))
    q.stop(workers)

    want = sum(range(n_msg))
    have = sum(msg.data[1] for msg in out.items())
    assert have == want, f"expect sum of {want} from processes"


def test_run_threads() -> None:
    """Run threads in parallel."""
    n_msg = 1000

    q, out = ezq.Q("thread"), ezq.Q("thread")
    workers = [
        ezq.run_thread(worker_sum, q, out, num=i) for i in range(ezq.NUM_THREADS)
    ]

    def wrap_lambda(i: int) -> Callable[[], int]:
        """Wrap a number in a lambda so thread-context works."""
        return lambda: i

    for num in range(n_msg):
        q.put(wrap_lambda(num))
    q.stop(workers)

    want = sum(range(n_msg))
    have = sum(msg.data[1] for msg in out.items())
    assert have == want, f"expect sum of {want} from threads"


def test_map() -> None:
    """Run a function on multiple processes and threads."""
    left = range(10)
    right = range(10, 0, -1)

    want = [a + b for (a, b) in zip(left, right)]
    have = list(ezq.map(operator.add, left, right))
    assert have == want, "expected subprocesses to work"

    # have = list(ezq.map(operator.add, left, right, kind="thread"))
    # assert have == want, "expected threads to work"
