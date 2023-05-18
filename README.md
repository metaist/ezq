# ezq

_Simple wrappers for python multiprocessing and threading._

[![Build Status](https://img.shields.io/github/actions/workflow/status/metaist/ezq/.github/workflows/ci.yaml?branch=main&style=for-the-badge)](https://github.com/metaist/ezq/actions)
[![ezq on PyPI](https://img.shields.io/pypi/v/ezq.svg?color=blue&style=for-the-badge)](https://pypi.org/project/ezq)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/ezq?style=for-the-badge)](https://pypi.org/project/ezq)

[Changelog] - [Issues] - [Documentation]

[changelog]: https://github.com/metaist/ezq/blob/main/CHANGELOG.md
[issues]: https://github.com/metaist/ezq/issues
[documentation]: https://metaist.github.io/ezq/

## Why?

`ezq` makes it easy to connect subprocesses and threads (both considered "workers") using queues with a simpler API than [`concurrent.futures`][1], [`multiprocessing`][2], or [`threading`][3].

[1]: https://docs.python.org/3/library/concurrent.futures.html
[2]: https://docs.python.org/3/library/multiprocessing.html
[3]: https://docs.python.org/3/library/threading.html

## Install

```bash
pip install ezq
```

## Example: Quick Start

If you just want to apply a function to some inputs, you can use `ezq.map()` to run it on all available CPUs and get the results back.

```python
import ezq
print(list(ezq.map(lambda x: x * 2, range(6))))
# => [0, 2, 4, 6, 8, 10]
```

## Example: Sum Messages

Here's a simple example of a worker that reads from an input queue, sums up the messages, and puts the result on an output queue.

```python
import ezq


def worker(q, out):
    """Add up all the messages."""
    total = 0
    for msg in q:  # read a message from the queue
        total += msg.data

    # after reading all the messages, write the total
    out.put(total)


def main():
    """Run several workers."""
    # Step 1: Creates the queues and start the workers.
    q, out = ezq.Q(), ezq.Q()  # input & output queues
    workers = [ezq.run(worker, q, out) for _ in range(ezq.NUM_CPUS)]
    # workers are all running

    # Step 2: Send work to the workers.
    for i in range(1000):
        q.put(i)  # send work

    # Step 3: Tell the workers to finish.
    q.stop(workers)
    # workers are all stopped

    # Step 4: Process the results.
    want = sum(range(1000))
    have = sum(msg.data for msg in out.items())
    assert have == want
    print(have)


if __name__ == "__main__":
    main()
```

## Typical worker lifecycle

- The main process [creates queues](#create-queues) with `ezq.Q`.

- The main process [creates workers](#create-workers) with `ezq.run` (alias for `Worker.process`) or `ezq.run_thread` (alias for `Worker.thread`).

- The main process [sends data](#send-data) using `Q.put`.

- The worker [iterates over the queue](#iterate-over-messages).

- The main process [ends the queue](#end-the-queue) with `Q.stop`.

- The worker returns when it reaches the end of the queue.

- (_Optional_) The main process [processes the results](#process-results).

## `Process` vs `Thread`

`ezq` supports two kinds of workers: `Process` and `Thread`. There is a lot of existing discussion about when to use which approach, but a general rule of thumb is:

- `Process` is for _parallelism_ so you can use multiple CPUs at once. Ideal for **CPU-bound** tasks like doing lots of mathematical calculations.

- `Thread` is for _concurrency_ so you can use a single CPU to do multiple things. Ideal for **I/O-bound** tasks like waiting for a disk, database, or network.

Some more differences:

- **Shared memory**: Each `Process` worker has [data sent to it via `pickle`](#beware-pickle) (actually [`dill`](https://github.com/uqfoundation/dill), a `pickle` replacement) and it doesn't share data with other workers. By contrast, each `Thread` worker shares its memory with all other workers on the same CPU, so it can [accidentally change global state](#beware-shared-state).

- **Queue overhead**: `ezq.Q` [has more overhead](#create-queues) for `Process` workers than `Thread` workers.

- **Creating sub-workers**: `Process` and `Thread` workers can create additional `Thread` workers, but [they cannot create additional `Process` workers](#create-workers).

## Create queues

In the main process, create the queues you'll need. Here are my common situations:

- **0 queues**: I'm using a simple function and can ask `ezq.map` to make the queues for me.

- **1 queue**: the worker reads from an input queue and persists the result somewhere else (e.g., writing to disk, making a network call, running some other program).

- **2 queues** (most common): the worker reads from an input queue and write the results to an output queue.

- **3 queues**: multiple stages of work are happening where workers are reading from one queue and writing to another queue for another worker to process.

**NOTE:** If you're using `Thread` workers, you can save some overhead by passing `Q("thread")`. This lightweight queue also doesn't use `pickle`, so you can use it to pass hard-to-pickle things (e.g., database connection).

```python
q, out = ezq.Q(), ezq.Q() # most common
q2 = ez.Q("thread") # only ok for Thread workers
```

## A worker task is just a function

In general, there's nothing special about a worker function, but note:

- If you're using `Process` workers, all arguments are [passed through `pickle` first](#beware-pickle).

- We don't currently do anything with the return value of this function (unless you use `ezq.map()`). You'll need an output queue to return data back to the main process/thread.

## Create workers

In the main process, create workers using `ezq.run` or `ezq.run_thread` which take a function and any additional parameters. Typically, you'll pass the queues you created to the workers at this point.

**NOTE:** `Process` and `Thread` workers can create additional `Thread` workers, but **they cannot create additional `Process` workers**.

## Send data

Once you've created the workers, you send them data with `Q.put` which creates `ezq.Msg` objects and puts them in the queue. Each message has three attributes (all optional):

- `data: Any` - This is the data you want the worker to work on.

- `kind: str` - You can use this to send multiple kinds of work to the same worker. Note that the special `END` kind is used to indicate the end of a queue.

- `order: int` - This is the message order which can help you reorder results or ensure that messages from a queue are read in a particular order (that's what `Q.sorted()` uses).

## Beware `pickle`

If you are using `Process` workers, everything passed to the worker (arguments, messages) is first passed to `pickle` (actually, [`dill`](https://github.com/uqfoundation/dill)). Anything that cannot be pickled with dill (e.g., database connections), cannot be passed to `Process` workers. Note that `dill` _can_ serialize many more types than `pickle` (e.g. `lambda` functions).

## Beware shared state

If you are using `Thread` workers, workers can share certain variables, so you need to be careful of how variables are access to avoid accidentally corrupting data.

## Iterate over messages

Inside the worker, iterate over the queue to read each message until the queue ends ([see below](#end-the-queue)). If the messages need to be processed in order, use `Q.sorted`.

```python
for msg in q: # read each message until the queue ends
  ...

for msg in q.sorted(): # read each message in order
  ...
```

## End the queue

After the main process has sent all the data to the workers, it needs to indicate
that there's no additional work to be done. This is done by calling `Q.stop()` using the input queue that the workers are reading from and passing the list of workers to wait for.

In some rare situations, you can use `Q.end()` to explicitly end the queue.

## Process results

If you have an output queue, you may want to to process the results. You can use `Q.items()` to end the queue and read the current messages.

```python
import ezq
out = ezq.Q()
...
result = [msg.data for msg in out.items()]
# OR
result = [msg.data for msg in out.items(sort=True)] # sorted by Msg.order
# OR
result = [msg.data for msg in out.items(cache=True)] # cache the messages
```

## Example: Read and Write Queues

In this example, several workers read from a queue, process data, and then write to a different queue that a single worker uses to print to the screen sorting the results as it goes along.

Note that we use a single `writer` to avoid clashes or overwriting.

```python
import ezq


def printer(out: ezq.Q) -> None:
    """Print results in increasing order."""
    for msg in out.sorted():
        print(msg.data)


def collatz(q: ezq.Q, out: ezq.Q) -> None:
    """Read numbers and compute values."""
    for msg in q:
        num = float(msg.data)
        if msg.kind == "EVEN":
            out.put((num, num / 2), order=msg.order)
        elif msg.kind == "ODD":
            out.put((num, 3 * num + 1), order=msg.order)


def main() -> None:
    """Run several threads with a subprocess for printing."""
    q, out = ezq.Q("thread"), ezq.Q()
    readers = [ezq.run_thread(collatz, q, out) for _ in range(ezq.NUM_THREADS)]
    writer = ezq.run(printer, out)

    for num in range(40):
        kind = "EVEN" if num % 2 == 0 else "ODD"
        q.put(num, kind=kind, order=num)

    q.stop(readers)
    out.stop(writer)


if __name__ == "__main__":
    main()
```

## License

[MIT License](https://github.com/metaist/ezq/blob/main/LICENSE.md)
