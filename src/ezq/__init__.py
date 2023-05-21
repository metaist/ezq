#!/usr/bin/env python
# coding: utf-8
"""Simple wrapper for python `multiprocessing` and `threading`.

.. include:: ../../README.md
   :start-line: 4
"""

__all__ = (
    "Task",
    "Context",
    "ContextName",
    "Msg",
    "END_MSG",
    "MsgQ",
    "NUM_CPUS",
    "NUM_THREADS",
    "IS_MACOS",
    "Worker",
    "Q",
    "run",
    "run_thread",
    "map",
)

# native
from dataclasses import dataclass
from operator import attrgetter
from os import cpu_count
from platform import system
from queue import Empty
from queue import Queue as ThreadSafeQueue
from threading import Thread
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Literal
from typing import Optional
from typing import Sequence
from typing import TYPE_CHECKING
from typing import Union

# lib
from multiprocess import Process  # type: ignore
from multiprocess import Queue

Task = Callable[..., Any]
"""Task function signature (any `Callable`)."""

Context = Union[Process, Thread]
"""Execution contexts (`Process`, `Thread`)."""

ContextName = Literal["process", "thread"]
"""Execution context names (`"process"`, `"thread"`)."""


@dataclass
class Msg:
    """Message for a queue."""

    data: Any = None
    """Message data to be transmitted."""

    kind: str = ""
    """Optional marker of message type."""

    order: int = 0
    """Optional ordering of messages."""


# NOTE: The python `queue.Queue` is not properly a generic.
# See: https://stackoverflow.com/a/48554601
if TYPE_CHECKING:  # pragma: no cover
    MsgQ = Union[Queue[Msg], ThreadSafeQueue]  # pylint: disable=unsubscriptable-object
else:
    MsgQ = Queue

END_MSG: Msg = Msg(kind="END")
"""Message that indicates no future messages will be sent."""

## Hardware-Specific Information ##

NUM_CPUS: int = cpu_count() or 1
"""Number of CPUs on this machine."""

NUM_THREADS: int = min(32, NUM_CPUS + 4)
"""Default number of threads (up to 32).

See: [CPython's default for this value][1].

[1]: https://github.com/python/cpython/blob/a635d6386041a2971cf1d39837188ffb8139bcc7/Lib/concurrent/futures/thread.py#L142
"""

IS_MACOS: bool = system().lower().startswith("darwin")
"""`True` if we're running on MacOS.

Currently, we only use this value for testing, but there are certain features that
do not work properly on MacOS.

See: [Example of MacOS-specific issues][1].

[1]: https://github.com/python/cpython/blob/c5b670efd1e6dabc94b6308734d63f762480b80f/Lib/multiprocessing/queues.py#L125
"""


class Worker:
    """A function running in a `Process` or `Thread`."""

    _worker: Context
    """Execution context."""

    @staticmethod
    def process(task: Task, *args: Any, **kwargs: Any) -> "Worker":
        """Create a `Process`-based `Worker`.

        Args:
            task (Task): function to run
            *args (Any): additional arguments to `task`
            **kwargs (Any): additional keyword arguments to `task`

        Returns:
            Worker: wrapped worker.
        """
        # NOTE: On MacOS, python 3.8 switched the default method
        # from "fork" to "spawn" because fork is considered dangerous.
        # Some posts say "forkserver" should be ok.
        # See:  https://bugs.python.org/issue?@action=redirect&bpo=33725
        #
        # if IS_MACOS:
        #     ctx = get_context("forkserver")
        # else:
        #     ctx = get_context()
        return Worker(Process(daemon=True, target=task, args=args, kwargs=kwargs))

    @staticmethod
    def thread(task: Task, *args: Any, **kwargs: Any) -> "Worker":
        """Create a `Thread`-based `Worker`.

        Args:
            task (Task): function to run
            *args (Any): additional arguments to `task`
            **kwargs (Any): additional keyword arguments to `task`

        Returns:
            Worker: wrapped worker.
        """
        return Worker(Thread(daemon=False, target=task, args=args, kwargs=kwargs))

    def __init__(self, context: Context):
        """Construct a worker from a context.

        Args:
            context (Context): a `Process` or a `Thread`
        """
        self._worker = context
        self._worker.start()

    def __getattr__(self, name: str) -> Any:
        """Delegate properties to the underlying task.

        Args:
            name (str): attribute name

        Returns:
            Any: attribute from the task
        """
        return getattr(self._worker, name)


class Q:
    """Simple message queue."""

    _q: MsgQ
    """Wrapped queue."""

    _cache: Optional[List[Msg]] = None
    """Cache of queue messages when calling `.items(cache=True)`."""

    _timeout: float = 0.05
    """Time in seconds to poll the queue."""

    def __init__(self, kind: ContextName = "process"):
        """Construct a queue wrapper.

        Args:
            kind (ContextName, optional): If `"thread"`, construct a lighter-weight
                `Queue` that is thread-safe. Otherwise, construct a full
                `multiprocess.Queue`. Defaults to `"process"`.
        """
        if kind == "process":
            self._q = Queue()
        elif kind == "thread":
            self._q = ThreadSafeQueue()
        else:  # pragma: no cover
            raise ValueError(f"Unknown queue type: {kind}")

    def __getattr__(self, name: str) -> Any:
        """Delegate properties to the underlying queue.

        Args:
            name (str): name of the attribute to access

        Returns:
            Any: attribute from the queue
        """
        return getattr(self._q, name)

    def __iter__(self) -> Iterator[Msg]:
        """Iterate over messages in a queue until `END_MSG` is received.

        Yields:
            Iterator[Msg]: iterate over messages in the queue
        """
        while True:
            try:
                msg = self._q.get(block=True, timeout=self._timeout)
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
            if self._cache is None:  # need to build a cache
                self.end()
                self._cache = list(self.sorted() if sort else self)
            return iter(self._cache)

        # not cached
        self.end()
        return self.sorted() if sort else iter(self)

    def sorted(self, start: int = 0) -> Iterator[Msg]:
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
            self._q.put(data)
        else:
            self._q.put(Msg(data=data, kind=kind, order=order))
        return self

    def end(self) -> "Q":
        """Add the `END_MSG` to indicate the end of work.

        Returns:
            Self: self for chaining
        """
        self._q.put(END_MSG)
        return self

    def stop(self, workers: Union[Worker, Sequence[Worker]]) -> "Q":
        """Use this queue to notify workers to end and wait for them to join.

        Args:
            workers (Worker, Sequence[Worker]): workers to wait for

        Returns:
            Self: self for chaining
        """
        _workers = [workers] if isinstance(workers, Worker) else workers

        for _ in range(len(_workers)):
            self.end()

        for task in _workers:
            task.join()

        return self


def run(task: Task, *args: Any, **kwargs: Any) -> Worker:
    """Run a function as a subprocess.

    Args:
        task (Task): function to run in each subprocess

        *args (Any): additional positional arguments to `task`.

        **kwargs (Any): additional keyword arguments to `task`.

    Returns:
        Worker: worker started in a subprocess

    .. changed:: 2.0.4
       This function now returns a `Worker` instead of a `Process`.
    """
    return Worker.process(task, *args, **kwargs)


def run_thread(task: Task, *args: Any, **kwargs: Any) -> Worker:
    """Run a function as a thread.

    Args:
        task (Task): function to run in each thread

        *args (Any): additional positional arguments to `task`.

        **kwargs (Any): additional keyword arguments to `task`.

    Returns:
        Worker: worker started in a thread

    .. changed:: 2.0.4
       This function now returns a `Worker` instead of a `Thread`.
    """
    return Worker.thread(task, *args, **kwargs)


def map(
    task: Task,
    *args: Iterable[Any],
    num: Optional[int] = None,
    kind: ContextName = "process",
) -> Iterator[Any]:
    """Call a function with arguments using multiple workers.

    Args:
        func (Callable): function to call

        *args (list[Any]): arguments to `func`. If multiple lists are provided,
            they will be passed to `zip` first.

        num (int, optional): number of workers. If `None`, `NUM_CPUS` or
            `NUM_THREADS` will be used as appropriate. Defaults to `None`.

        kind (ContextName, optional): execution context to use.
            Defaults to `"process"`.

    Yields:
        Any: results from applying the function to the arguments
    """
    q, out = Q(kind=kind), Q(kind=kind)

    def worker(_q: Q, _out: Q) -> None:
        """Internal call to `func`."""
        for msg in _q.sorted():
            _out.put(data=task(*msg.data), order=msg.order)

    if kind == "process":
        workers = [Worker.process(worker, q, out) for _ in range(num or NUM_CPUS)]
    elif kind == "thread":
        workers = [Worker.thread(worker, q, out) for _ in range(num or NUM_THREADS)]
    else:  # pragma: no cover
        raise ValueError(f"Unknown worker context: {kind}")

    for order, value in enumerate(zip(*args)):
        q.put(value, order=order)
    q.stop(workers)

    for msg in out.end().sorted():
        yield msg.data
