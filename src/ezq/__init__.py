#!/usr/bin/env python
# coding: utf-8
"""Simple wrapper for python multiprocessing."""

# native
from dataclasses import dataclass
from multiprocessing import Process, Queue
from os import cpu_count
from typing import Any, Callable, List, Iterator, Union
import queue

# pkg
from .__about__ import (
    __url__,
    __version__,
    __pubdate__,
    __author__,
    __email__,
    __copyright__,
    __license__,
)


@dataclass
class Msg:
    """Message for a queue."""

    kind: str = ""
    data: Any = None
    order: int = 0


END_MSG: Msg = Msg(kind="END")
"""Message that indicates no future messages will be sent."""


NUM_CPUS: int = cpu_count() or 1
"""Number of CPUs on this machine."""


def iter_msg(q: Queue, timeout=0.05) -> Iterator[Msg]:
    """Yield messages in a queue until an `END_MSG` is received.

    Args:
        q (Queue): queue to read from
        timeout (float, optional): time in seconds to poll the queue. Defaults to 0.05.

    Yields:
        Iterator[Msg]: iterate over messages in the queue
    """
    while True:
        try:
            msg = q.get(block=True, timeout=timeout)
            if msg.kind == END_MSG.kind:
                break
            yield msg
        except queue.Empty:  # pragma: no cover
            continue


def iter_sortq(
    q: Queue, start: int = 0, key: Callable = lambda m: m.order
) -> Iterator[Msg]:
    """Yield messages in a particular order.

    NOTE: Message order must be monotonically increasing. If there are any gaps, messages
    after the gap won't be yielded until the input queue ends.

    Args:
        q (Queue): queue to read from
        start (int, optional): initial message number. Defaults to 0.
        key (Callable, optional): custom key function. Defaults to `lambda m: m.order`.

    Yields:
        Iterator[Msg]: message yielded in the correct order
    """
    prev = start - 1
    waiting = []
    for msg in iter_msg(q):
        waiting.append(msg)
        waiting = sorted(waiting, key=key, reverse=True)
        while waiting and key(waiting[-1]) == prev + 1:
            prev += 1
            yield waiting.pop()

    # input queue ended; yield any waiting messages
    while waiting:
        yield waiting.pop()


def run(func: Callable, *args, **kwargs) -> Process:
    """Run a function as a subprocess.

    Args:
        func (Callable): function to run in each subprocess
        *args (Any): additional positional arguments to `func`.
        **kwargs (Any): additional keyword arguments to `func`.

    Returns:
        Process: subprocess that was started
    """
    proc = Process(daemon=True, target=func, args=args, kwargs=kwargs)
    proc.start()
    return proc


def endq(q: Queue, count: int = 1) -> Queue:
    """Add a message to a queue to indicate its end.

    Args:
        q (Queue): queue on which to send the message
        count (int): number of times to send the message. Defaults to 1.

    Returns:
        Queue: queue on which to send the message
    """
    for _ in range(count):
        q.put(END_MSG)
    return q


def endq_and_wait(q: Queue, procs: Union[Process, List[Process]]) -> List[Process]:
    """Notify a list of processes to end and wait for them to join.

    Args:
        q (Queue): subprocess input queue
        procs (Process | List[Process]): processes to wait for

    Returns:
        List[Process]: subprocesses that ended
    """
    if isinstance(procs, Process):
        procs = [procs]

    endq(q, len(procs))
    for proc in procs:
        proc.join()
    return procs
