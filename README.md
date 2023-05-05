# ezq

_Simple wrappers for python multiprocessing._

[![Build Status](https://img.shields.io/github/actions/workflow/status/metaist/ezq/.github/workflows/ci.yaml?branch=main&style=for-the-badge)](https://github.com/metaist/ezq/actions)
[![ezq on PyPI](https://img.shields.io/pypi/v/ezq.svg?color=blue&style=for-the-badge)](https://pypi.org/project/ezq)

[Changelog] - [Issues] - [Documentation]

[changelog]: https://github.com/metaist/ezq/blob/main/CHANGELOG.md
[issues]: https://github.com/metaist/ezq/issues
[documentation]: https://metaist.github.io/ezq/

## Why?

Even though [`multiprocessing`][1] has `Pool` and `Queue`, it's surprisingly difficult
to get started to do slightly more complex workflows. `ezq` makes it easy to connect subprocesses (workers) using queues.

[1]: https://docs.python.org/3/library/multiprocessing.html

## Install

```bash
pip install ezq
```

## Example: Sum Messages

Here's a simple example of a worker that reads from an input queue, sums up the
messages, and puts the result on an output queue.

```python
import ezq


def worker(in_q, out_q):
    """Add up all the messges."""
    count = 0
    for msg in ezq.iter_msg(in_q):
        # you could check `msg.kind` if there's different kinds of work
        count += msg.data

    # when `in_q` is done, put the result on `out_q`
    ezq.put_msg(out_q, data=count)


def main():
    """Run several workers."""
    in_q = ezq.Queue()  # to send work
    out_q = ezq.Queue()  # to get results

    workers = [ezq.run(worker, in_q, out_q) for _ in range(ezq.NUM_CPUS)]
    # workers started

    for i in range(1000):
        ezq.put_msg(in_q, data=i)  # send work

    ezq.endq_and_wait(in_q, workers)
    # all workers are done

    result = sum(msg.data for msg in ezq.iter_q(out_q))
    assert result == sum(x for x in range(1000))
    print(result)


if __name__ == "__main__":
    main()
```

## Typical worker lifecycle

- The main process [creates workers](#create-workers) with `ezq.run`.

- The main process [sends data](#send-data) with `ezq.put_msg`.

- The worker [iterates over the queue](#iterate-over-messages) with `ezq.iter_msg`.

- The main process [ends the queue](#end-the-queue) with `ezq.endq_and_wait`.

- The worker returns when it reaches the end of the queue.

## A worker is just a function

In general, there's nothing special about a worker function, but note:

- All arguments are passed through `pickle` first ([see below](#beware-pickle)).

- We don't currently do anything with the return value of this function. You'll
  need an output queue to return data back to the main process.

## Create workers

In the main process, create workers using `ezq.run` which takes a function and
any additional parameters. Note that **workers cannot create additional workers**.

## Send data

Once you've started the workers, you send them data by calling with `ezq.put_msg`
which creates `ezq.Msg` objects and puts them in the queue. There are three
attributes that are sent (all optional):

- `kind` - a string that indicates what kind of message it is.
  You can use this to send multiple kinds of work to the same worker.
  Note that the special `END` kind is used to indicate the end of a queue
  (that's what `ezq.endq` sends).

- `data` - anything that can be pickled.
  This is the data you want the worker to work on.

- `order` - an integer that indicates the message order.
  This can help you reorder results or ensure that messages from a queue are
  read in a particular order (that's what `ezq.sortiter` uses).

## Beware `pickle`

All parameters sent to workers in `ezq.run` and any values put in queues
using `ezq.put_msg` are first passed to `pickle` by [`multiprocessing`][1]
so anything that cannot be pickled (e.g., database connection)
cannot be passed to workers.

## Iterate over messages

Inside the worker, use `ezq.iter_msg` to iterate over the messages in the queue
until the queue ends ([see below](#end-the-queue)). If the messages need to be
sorted first, wrap the call with `ezq.sortiter`.

If you need to read all the messages currently in the queue, you can use `ezq.iter_q`
which will immediately end the queue and return results. You can also wrap this call
in `ezq.sortiter` if you need the messages to be sorted first.

## End the queue

After the main process has sent all the data to the workers, it needs to indicate
that there's no additional work to be done. This is done by putting a special
`ezq.END_MSG` in the queue which is processed by `ezq.iter_msg` and never seen by
the workers.

There are three ways a queue can be ended:

- `ezq.endq` - Explicitly end a queue. You normally won't need to call this.

- `ezq.iter_q` - End a queue and iterate over the current messages. This is
  useful when processing an output queue back in the main process.

- `ezq.endq_and_wait` - End a queue and wait for the workers to finish. The most
  common way to end a queue. You'll need to call this before the end of your main
  process in order to get results back from all the workers.

## Example: Read and Write Queues

In this example, several workers read from a queue, process data, and then write to a
different queue that a single worker uses to print to the screen sorting the results as
it goes along. When interfacing with a single I/O device (e.g., screen, file) we typically use a single worker to avoid clashes or overwriting.

```python
import ezq


def printer(write_q):
    """Print results in increasing order."""
    for msg in ezq.sortiter(ezq.iter_msg(write_q)):
        print(msg.data)


def collatz(read_q, write_q):
    """Read numbers and compute values."""
    for msg in ezq.iter_msg(read_q):
        num = msg.data
        if msg.kind == "EVEN":
            ezq.put_msg(write_q, data=(num, num / 2), order=msg.order)
        elif msg.kind == "ODD":
            ezq.put_msg(write_q, data=(num, 3 * num + 1), order=msg.order)


def main():
    """Run several subprocesses."""
    read_q, write_q = ezq.Queue(), ezq.Queue()
    readers = [ezq.run(collatz, read_q, write_q) for _ in range(ezq.NUM_CPUS - 1)]
    writers = ezq.run(printer, write_q)

    for i in range(40):
        kind = "EVEN" if i % 2 == 0 else "ODD"
        ezq.put_msg(read_q, kind=kind, data=i, order=i)

    ezq.endq_and_wait(read_q, readers)
    ezq.endq_and_wait(write_q, writers)


if __name__ == "__main__":
    main()
```

## License

[MIT License](https://github.com/metaist/ezq/blob/main/LICENSE.md)
