#!/usr/bin/env python
# coding: utf-8
"""Simple wrapper for python multiprocessing.

.. include:: ../../README.md
   :start-line: 4
"""

__all__ = (
    "Process",
    "Queue",
    "__url__",
    "__version__",
    "__pubdate__",
    "__author__",
    "__email__",
    "__copyright__",
    "__license__",
    "Msg",
    "END_MSG",
    "NUM_CPUS",
    "iter_msg",
    "iter_q",
    "sortiter",
    "run",
    "put_msg",
    "endq",
    "endq_and_wait",
)

# native
from dataclasses import dataclass
from multiprocessing import Process, Queue, queues
from operator import attrgetter
from os import cpu_count
from queue import Empty
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Iterator,
    Optional,
    Union,
    TYPE_CHECKING,
)


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

# NOTE: The python queue.Queue is not properly a generic.
# See: https://stackoverflow.com/a/48554601
if TYPE_CHECKING:  # pragma: no cover
    MsgQ = queues.Queue[Msg]  # pylint: disable=unsubscriptable-object
else:
    MsgQ = queues.Queue


def iter_msg(
    q: MsgQ, block: bool = True, timeout: Optional[float] = 0.05
) -> Iterator[Msg]:
    """Iterate over messages in a queue.

    Args:
        q (Queue[Msg]): queue to read from
        block (bool, optional): block if necessary until an item is available. Defaults to True.
        timeout (float, optional): time in seconds to poll the queue. Defaults to 0.05.

    Yields:
        Iterator[Msg]: iterate over messages in the queue
    """
    while True:
        try:
            msg = q.get(block=block, timeout=timeout)
            if msg.kind == END_MSG.kind:
                # We'd really like to put the `END_MSG` back in the queue
                # to prevent reading past the end, but in practice
                # this often creates an uncatchable `BrokenPipeError`.
                # q.put(END_MSG)
                break
            yield msg
        except Empty:  # pragma: no cover
            # queue might not actually be empty
            # see: https://bugs.python.org/issue20147
            continue


def iter_q(q: MsgQ) -> Iterator[Msg]:
    """End a queue and iterate over its current messages.

    Args:
        q (Queue[Msg]): queue to read from

    Yields:
        Iterator[Msg]: iterate over messages in the queue
    """
    endq(q)  # ensure queue has an end
    return iter_msg(q, block=False, timeout=None)


def sortiter(
    items: Iterable[Any],
    start: int = 0,
    key: Callable[[Any], int] = attrgetter("order"),
) -> Iterator[Any]:
    """Sort and yield the contents of a generator.

    NOTE: `key` must return values that increment by one for each item. If there
    are any gaps, items after the gap won't be yielded until the end.

    Args:
        items (Iterable): iterable to sort
        start (int, optional): initial order number. Defaults to 0.
        key (Callable, optional): custom key function.
            Defaults to sorting by the `order` attribute.

    Yields:
        Iterator[Any]: item yielded in the correct order
    """
    prev = start - 1
    waiting: List[Any] = []
    for item in items:
        if not waiting and key(item) == prev + 1:
            prev += 1
            yield item
            continue

        # items came out of order
        waiting.append(item)
        waiting = sorted(waiting, key=key, reverse=True)
        while waiting and key(waiting[-1]) == prev + 1:
            prev += 1
            yield waiting.pop()

    # generator ended; yield any waiting items
    while waiting:
        yield waiting.pop()


def run(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Process:
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


def put_msg(q: MsgQ, kind: str = "", data: Any = None, order: int = 0) -> MsgQ:
    """Put a message into a queue.

    Args:
        q (Queue[Msg]): queue to add message to
        kind (str, optional): kind of message. Defaults to "".
        data (Any, optional): message data. Defaults to None.
        order (int, optional): message order. Defaults to 0.

    Returns:
        Queue[Msg]: queue the message was added to
    """
    q.put(Msg(kind, data, order))
    return q


def endq(q: MsgQ) -> MsgQ:
    """Add a message to a queue to indicate its end.

    Args:
        q (Queue[Msg]): queue on which to send the message

    Returns:
        Queue[Msg]: queue the message was sent on
    """
    q.put(END_MSG)
    return q


def endq_and_wait(q: MsgQ, procs: Union[List[Process], Process]) -> List[Process]:
    """Notify a list of processes to end and wait for them to join.

    Args:
        q (Queue[Msg]): subprocess input queue
        procs (Union[Process, List[Process]]): processes to wait for

    Returns:
        List[Process]: subprocesses that ended
    """
    if isinstance(procs, Process):
        procs = [procs]

    for _ in range(len(procs)):
        endq(q)

    for proc in procs:
        proc.join()
    return procs
