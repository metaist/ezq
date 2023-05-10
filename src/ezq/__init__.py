#!/usr/bin/env python
# coding: utf-8
"""Simple wrapper for python `multiprocessing` and `threading`.

.. include:: ../../README.md
   :start-line: 4
"""

__all__ = (
    "__author__",
    "__copyright__",
    "__email__",
    "__license__",
    "__pubdate__",
    "__url__",
    "__version__",
    #
    ## imported classes ##
    # "Process",  # deprecated
    "Queue",  # deprecated
    # "Thread",  # deprecated
    # "ThreadSafeQueue",  # deprecated
    #
    ## types ##
    # "MsgQ",
    # "Worker",
    # "Workers",
    # "SomeWorkers",
    #
    ## classes ##
    "Msg",
    "Q",
    #
    ## constants ##
    "NUM_CPUS",
    "NUM_THREADS",
    "END_MSG",
    #
    ## functions ##
    "run",
    "run_thread",
    "map",
    "put_msg",  # deprecated
    "iter_msg",  # deprecated
    "iter_q",  # deprecated
    "sortiter",  # deprecated
    "endq",  # deprecated
    "endq_and_wait",  # deprecated
)

# native
from dataclasses import dataclass
from multiprocessing import Process, Queue
from operator import attrgetter
from os import cpu_count
from queue import Empty, Queue as ThreadSafeQueue
from threading import Thread
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Sequence,
    Iterator,
    Optional,
    Union,
    TYPE_CHECKING,
)
from typing_extensions import deprecated, Self


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
    """Optional marker of message type."""

    data: Any = None
    """Message data to be transmitted."""

    order: int = 0
    """Optional ordering of messages."""


END_MSG: Msg = Msg(kind="END")
"""Message that indicates no future messages will be sent."""

NUM_CPUS: int = cpu_count() or 1
"""Number of CPUs on this machine."""

NUM_THREADS: int = min(32, NUM_CPUS + 4)
"""Default number of threads (up to 32).

See: [CPython's default for this value][1].

[1]: https://github.com/python/cpython/blob/a635d6386041a2971cf1d39837188ffb8139bcc7/Lib/concurrent/futures/thread.py#L142
"""

# NOTE: The python `queue.Queue` is not properly a generic.
# See: https://stackoverflow.com/a/48554601
if TYPE_CHECKING:  # pragma: no cover
    MsgQ = Union[Queue[Msg], ThreadSafeQueue]  # pylint: disable=unsubscriptable-object
else:
    MsgQ = Queue

Worker = Union[Thread, Process]
"""A thread or a process."""

Workers = Union[Sequence[Thread], Sequence[Process]]
"""Multiple threads or processes."""

SomeWorkers = Union[Worker, Workers]
"""One or more threads or processes."""


def run(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Process:
    """Run a function as a subprocess.

    Args:
        func (Callable): function to run in each subprocess
        *args (Any): additional positional arguments to `func`.
        **kwargs (Any): additional keyword arguments to `func`.

    Returns:
        Process: subprocess that was started
    """
    worker = Process(daemon=True, target=func, args=args, kwargs=kwargs)
    worker.start()
    return worker


def run_thread(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Thread:
    """Run a function as a thread.

    Args:
        func (Callable): function to run in each thread
        *args (Any): additional positional arguments to `func`.
        **kwargs (Any): additional keyword arguments to `func`.

    Returns:
        Thread: thread that was started
    """
    worker = Thread(daemon=False, target=func, args=args, kwargs=kwargs)
    worker.start()
    return worker


map_ = map  # save the value of the builtin


def map(
    func: Callable[..., Any],
    *args: Iterable[Any],
    num: Optional[int] = None,
    thread: bool = False,
) -> Iterator[Any]:
    """Call a function with arguments using multiple workers.

    Args:
        func (Callable): function to call
        *args (list[Any]): arguments to `func`. If multiple lists are provided,
            they will be passed to `zip` first.
        num (int, optional): number of workers. If `None`, `NUM_CPUS` or
            `NUM_THREADS` will be used as appropriate. Defaults to `None`.
        thread (bool, optional): whether to use threads instead of processes.
            Defaults to `False`.

    Yields:
        Any: results from applying the function to the arguments
    """
    q, out = Q(thread=thread), Q(thread=thread)

    def _worker(_q: Q, _out: Q) -> None:
        """Internal worker that calls `func`."""
        for msg in _q.sorted():
            _out.put(data=func(*msg.data), order=msg.order)

    workers: Workers
    if thread:
        workers = [run_thread(_worker, q, out) for _ in range(num or NUM_THREADS)]
    else:
        workers = [run(_worker, q, out) for _ in range(num or NUM_CPUS)]

    for order, value in enumerate(zip(*args)):
        q.put(value, order=order)
    q.stop(workers)

    for msg in out.end().sorted():
        yield msg.data


@deprecated("Use Q.put(data) instead.")
def put_msg(q: MsgQ, kind: str = "", data: Any = None, order: int = 0) -> MsgQ:
    """Put a message into a queue.

    Args:
        q (Queue[Msg]): queue to add message to
        kind (str, optional): kind of message. Defaults to "".
        data (Any, optional): message data. Defaults to None.
        order (int, optional): message order. Defaults to 0.

    Returns:
        Queue[Msg]: queue the message was added to

    .. deprecated:: 2.0.3
       Use `Q.put` instead.
    """
    q.put(Msg(kind=kind, data=data, order=order))
    return q


@deprecated("Use iter(Q) instead.")
def iter_msg(
    q: MsgQ, block: bool = True, timeout: Optional[float] = 0.05
) -> Iterator[Msg]:
    """Iterate over messages in a queue.

    Args:
        q (Queue[Msg]): queue to read from
        block (bool, optional): block until an item is available. Defaults to `True`.
        timeout (float, optional): time in seconds to poll the queue.
            Defaults to `0.05`.

    Yields:
        Iterator[Msg]: iterate over messages in the queue

    .. deprecated:: 2.0.3
       Use `iter(Q)` instead.
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


@deprecated("Use Q.items() instead.")
def iter_q(q: MsgQ) -> Iterator[Msg]:
    """End a queue and iterate over its current messages.

    Args:
        q (Queue[Msg]): queue to read from

    Yields:
        Iterator[Msg]: iterate over messages in the queue

    .. deprecated:: 2.0.3
       Use `Q.items()` instead.
    """
    endq(q)  # ensure queue has an end
    return iter_msg(q, block=False, timeout=None)


@deprecated("Use Q.sorted() instead.")
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

    .. deprecated:: 2.0.3
       Use `Q.sorted()` instead.
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
        waiting.sort(key=key, reverse=True)  # sort in-place for performance
        while waiting and key(waiting[-1]) == prev + 1:
            prev += 1
            yield waiting.pop()

    # generator ended; yield any waiting items
    while waiting:
        yield waiting.pop()


@deprecated("Use Q.end() instead.")
def endq(q: MsgQ) -> MsgQ:
    """Add a message to a queue to indicate its end.

    Args:
        q (Queue[Msg]): queue on which to send the message

    Returns:
        Queue[Msg]: queue the message was sent on

    .. deprecated:: 2.0.3
       Use `Q.end()` instead.
    """
    q.put(END_MSG)
    return q


@deprecated("Use Q.stop(workers) instead.")
def endq_and_wait(q: MsgQ, workers: SomeWorkers) -> Workers:
    """Notify a list of workers to end and wait for them to join.

    Args:
        q (Queue[Msg]): worker queue
        workers (Worker, Sequence[Worker]): workers to wait for

    Returns:
        List[Thread|Process]: threads or subprocesses that ended

    .. deprecated:: 2.0.3
       Use `Q.stop()` instead.
    """
    # We're a little verbose to placate the type-checker.
    _workers: Workers
    if isinstance(workers, Thread):
        _workers = [workers]
    elif isinstance(workers, Process):
        _workers = [workers]
    else:
        _workers = workers

    for _ in range(len(_workers)):
        endq(q)

    for worker in _workers:
        worker.join()
    return _workers


class Q:
    """A simple message queue."""

    q: MsgQ
    """Wrapped queue."""

    _items: Optional[List[Msg]] = None
    """Cache of queue messages when calling `.items(cache=True)`."""

    def __init__(self, thread: bool = False, *args: Any, **kwargs: Any):
        """Construct a queue wrapper.

        Args:
            thread (bool, optional): If `True`, construct a lighter-weight
                `Queue` that is thread-safe. Otherwise, construct a full
                `multiprocessing.Queue`. Defaults to `False`.

            *args, *kwargs: Additional arguments passed to the `Queue` constructor.
        """
        if thread:
            self.q = ThreadSafeQueue(*args, **kwargs)
        else:
            self.q = Queue(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Delegate properties to the underlying queue.

        Args:
            name (str): name of the attribute to access

        Returns:
            Any: attribute from the queue
        """
        return getattr(self.q, name)

    def __iter__(self) -> Iterator[Msg]:
        """Iterate over messages in a queue until `END_MSG` is received.

        Yields:
            Iterator[Msg]: iterate over messages in the queue
        """
        return iter_msg(self.q)

    def items(self, cache: bool = False, sort: bool = False) -> Iterator[Msg]:
        """End a queue and read all the current messages.

        Args:
            cache (bool, optional): if `True`, cache the messages. This allows you
                to call this method multiple times to get the same messages.
                Defaults to `False`.

            sort (bool, optional): if `True` messages are sorted by `Msg.order`.
                Defaults to `False`.

        Yields:
            Iterator[Msg]: iterate over messages in the queue
        """
        if cache:
            if self._items is None:  # need to build a cache
                self.end()
                self._items = list(self.sorted() if sort else self)
            return iter(self._items)

        # not cached
        self.end()
        return self.sorted() if sort else iter(self)

    def sorted(self) -> Iterator[Msg]:
        """Iterate over messages in a sorted order.

        See: `ezq.sortiter`

        Yields:
            Iterator[Msg]: sorted message iterator
        """
        return sortiter(self)

    def put(self, data: Any = None, kind: str = "", order: int = 0) -> Self:
        """Put a message on the queue.

        Args:
            data (Any, optional): message data. Defaults to `None`.
            kind (str, optional): kind of message. Defaults to `""`.
            order (int, optional): message order. Defaults to `0`.

        Returns:
            Self: self for chaining
        """
        if isinstance(data, Msg):
            self.q.put_nowait(data)
        else:
            self.q.put_nowait(Msg(data=data, kind=kind, order=order))
        return self

    def end(self) -> Self:
        """Add the `END_MSG` to indicate the end of work.

        Returns:
            Self: self for chaining
        """
        self.q.put(END_MSG)
        return self

    def stop(self, workers: SomeWorkers) -> Self:
        """Use this queue to notify workers to end and wait for them to join.

        Args:
            workers (Worker, Sequence[Worker]): workers to wait for

        Returns:
            Self: self for chaining
        """
        endq_and_wait(self.q, workers)
        return self
