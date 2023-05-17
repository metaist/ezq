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

    data: Any = None
    """Message data to be transmitted."""

    kind: str = ""
    """Optional marker of message type."""

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

Task = Callable[..., Any]
"""Task function signature."""

Context = Union[Process, Thread]
"""Execution contexts."""

ContextName = Literal["process", "thread"]
"""Execution context names."""


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


class Q:
    """Simple message queue."""

    q: MsgQ
    """Wrapped queue."""

    _items: Optional[List[Msg]] = None
    """Cache of queue messages when calling `.items(cache=True)`."""

    timeout: float = 0.05
    """Time in seconds to poll the queue."""

    def __init__(self, kind: ContextName = "process"):
        """Construct a queue wrapper.

        Args:
            kind (ContextName, optional): If `"thread"`, construct a lighter-weight
                `Queue` that is thread-safe. Otherwise, construct a full
                `multiprocessing.Queue`. Defaults to `"process"`.
        """
        if kind == "process":
            self.q = Queue()
        elif kind == "thread":
            self.q = ThreadSafeQueue()
        else:  # pragma: no cover
            raise ValueError(f"Unknown queue type: {kind}")

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
        while True:
            try:
                msg = self.q.get(block=True, timeout=self.timeout)
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

    def sorted(self, start=0) -> Iterator[Msg]:
        """Iterate over messages sorted by `Msg.order`.

        NOTE: `Msg.order` must be incremented by one for each message.
        If there are any gaps, messages after the gap won't be yielded
        until the end.

        Args:
            start (int, optional): initial message number. Defaults to `0`.

        Yields:
            Iterator[Msg]: message yielded in the correct order
        """
        prev = start - 1
        key = attrgetter("order")
        waiting: List[Msg] = []
        for item in self:
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

    def put(self, data: Any = None, *, kind: str = "", order: int = 0) -> "Q":
        """Put a message on the queue.

        Args:
            data (Any, optional): message data. Defaults to `None`.
            kind (str, optional): kind of message. Defaults to `""`.
            order (int, optional): message order. Defaults to `0`.

        Returns:
            Self: self for chaining
        """
        if isinstance(data, Msg):
            self.q.put(data)
        else:
            self.q.put(Msg(data=data, kind=kind, order=order))
        return self

    def end(self) -> "Q":
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
