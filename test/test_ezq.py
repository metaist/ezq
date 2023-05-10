#!/usr/bin/env python
# coding: utf-8
"""Test ezq functions."""

# native
import operator
from typing import Callable

# pkg
import ezq


# functional API (deprecated) #


def test_functional_api() -> None:
    """Run workers using the functional API (deprecated)."""

    def worker_f(q: ezq.MsgQ, out: ezq.MsgQ) -> None:
        """Internal worker."""
        for msg in ezq.iter_msg(q):
            ezq.put_msg(out, data=msg.data + 1, order=msg.order)

    q: ezq.MsgQ = ezq.Queue()
    out: ezq.MsgQ = ezq.Queue()
    process = ezq.run(worker_f, q, out)

    q2: ezq.MsgQ = ezq.Q(thread=True).q
    out2: ezq.MsgQ = ezq.Q(thread=True).q
    thread = ezq.run_thread(worker_f, q2, out2)

    for i in range(10):
        ezq.put_msg(q, data=i, order=i)
        ezq.put_msg(q2, data=i, order=i)

    ezq.endq_and_wait(q, process)
    ezq.endq_and_wait(q2, thread)

    want = [x + 1 for x in range(10)]

    have = [msg.data for msg in ezq.sortiter(ezq.iter_q(out))]
    assert have == want, "expected subprocesses to work"

    have = [msg.data for msg in ezq.sortiter(ezq.iter_q(out2))]
    assert have == want, "expected threads to work"


def test_q_wrapper() -> None:
    """Use underlying queue."""
    q = ezq.Q(thread=True)
    q.put(1)
    q.put(ezq.Msg(data=2))

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

    for num in range(n_msg):
        q.put(ezq.Msg(data=num))
    q.stop(workers)

    want = sum(range(n_msg))
    have = sum(msg.data[1] for msg in out.items())
    assert have == want, f"expect sum of {want} from processes"


def test_run_threads() -> None:
    """Run threads in parallel."""
    n_msg = 1000

    q, out = ezq.Q(thread=True), ezq.Q(thread=True)
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
    """Run a function on multiple threads."""
    left = range(10)
    right = range(10, 0, -1)

    want = [a + b for (a, b) in zip(left, right)]

    have = list(ezq.map(operator.add, left, right, thread=True))
    assert have == want, "expected threads to work"

    have = list(ezq.map(operator.add, left, right))
    assert have == want, "expected subprocesses to work"
