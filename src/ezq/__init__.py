#!/usr/bin/env python
# coding: utf-8
"""Simple wrapper for python multiprocessing."""

# native
from dataclasses import dataclass
from functools import partial
from multiprocessing import Process, Queue
from os import cpu_count
from typing import Any, Callable, List, Iterator
import queue
import signal

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


END_MSG = Msg(kind="END")
"""Message that indicates no future messages will be sent."""

IS_ALIVE = True
"""Whether the process is alive. NOTE: Setting to True will prevent `queuer` from working."""

NUM_CPUS = cpu_count() or 1
"""Number of CPUs on this machine."""

Daemon = lambda target: Process(daemon=True, target=target)


def stop_iter_msg():
    """Stop `iter_msg` by setting `IS_ALIVE` to `False`."""
    global IS_ALIVE  # pylint: disable=global-statement
    IS_ALIVE = False


def iter_msg(q: Queue, timeout=0.05) -> Iterator[Msg]:
    """Yield messages for a queue.

    Note, this function checks whether the global `IS_ALIVE` value is `True`. If it
    is set to `False`, the queuer will immediately stop.

    Args:
        q (Queue): queue to read from
        timeout (float, optional): time in seconds to poll the queue. Defaults to 0.05.

    Returns:
        None

    Yields:
        Iterator[Msg]: message in the queue
    """
    while IS_ALIVE:
        try:
            msg = q.get(block=True, timeout=timeout)
            if msg.kind == END_MSG.kind:
                break
            yield msg
        except queue.Empty:  # pragma: no cover
            continue


def start_processes(procs: List[Process]) -> List[Process]:
    """Return a list of subprocesses after starting them.

    Args:
        procs (List[Process]): list of subprocesses to start

    Returns:
        List[Process]: subprocesses that were started
    """
    for proc in procs:
        proc.start()
    return procs


def start(worker: Callable, count: int = NUM_CPUS) -> List[Process]:
    """Start a worker as several subprocesses.

    Args:
        worker (Callable): function to run in each subprocess
        count (int, optional): number of subprocesses to start. Defaults to NUM_CPUS.

    Returns:
        List[Process]: subprocesses that were started
    """
    return start_processes([Daemon(worker) for _ in range(count)])


def start_numbered(worker: Callable, count: int = NUM_CPUS) -> List[Process]:
    """Start a worker and pass it its number.

    This is useful, for example, when using `tqdm` and you want to set the position.

    Args:
        worker (Callable): function to run in each subprocess
            (NOTE: must take a `num` parameter of type `int`)
        count (int, optional): number of subprocesses to start. Defaults to NUM_CPUS.

    Returns:
        List[Process]: subprocesses that were started
    """
    return start_processes([Daemon(partial(worker, num=n)) for n in range(count)])


def wait(q: Queue, procs: List[Process]):
    """Notify a list of processes to end and wait for them to join.

    Args:
        q (Queue): queue to put the end message on
        procs (List[Process]): processes to wait for
    """
    for _ in range(len(procs)):
        q.put(END_MSG)
    # all processes notified

    for proc in procs:
        proc.join()
    # all processes ended


signal.signal(signal.SIGINT, stop_iter_msg)
