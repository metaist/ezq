# ezq - Simple wrappers for python multiprocessing

## Purpose

An easy way to get started using queues and [`multiprocessing`] in python for CPU-heavy
work. Use [`threading`] for I/O heavy work.

The general idea is that you connect workers (subprocesses) with queues.

[`multiprocessing`]: https://docs.python.org/3/library/multiprocessing.html
[`threading`]: https://docs.python.org/3/library/threading.html

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
    out_q.put(ezq.Msg(data=count))


def main():
    """Run several workers."""
    in_q = ezq.Queue()  # to send work
    out_q = ezq.Queue()  # to get results

    workers = [ezq.run(worker, in_q, out_q) for _ in range(ezq.NUM_CPUS)]
    # workers started

    for i in range(1000):
        in_q.put(ezq.Msg(data=i))  # send work

    ezq.endq_and_wait(in_q, workers)  # end work queue and wait for workers to finish
    ezq.endq(out_q)  # end result queue so we can iterate over it

    result = sum(msg.data for msg in ezq.iter_msg(out_q))
    assert result == sum(x for x in range(1000))
    print(result)


if __name__ == "__main__":
    main()
```

## Key Concepts

### `ezq.run` creates workers

You create subprocesses (workers) using `ezq.run` which takes a function and any
additional parameters to send to the function. You'll generally want to pass in a queue
that you can use to send work to the worker. This will also be the way to notify the
worker that there's no additional work to be done.

### Parameters to workers and queue contents are sent using `pickle`

Note that the additional parameters sent to a worker are first passed to `pickle` so
certain types of data (e.g., custom classes) many not work. The same is true for the data
that is put into a `ezq.Msg`.

### Work is sent via `ezq.Msg` objects

Once you've set up the workers, you send them work by putting `ezq.Msg` objects in the
queue. An `ezq.Msg` object has three attributes:

- `.kind` - a string that indicates what kind of message it is. You can use this to send
  multiple kinds of work to the same worker. Note that the special `END` kind is used to
  indicate the end of a queue (that's what `ezq.endq` sends).

- `.data` - anything that can be pickled. This is the data you want the worker to work on.

- `.order` - an integer that indicates the message order. This can help you reorder results
  or ensure that messages from a queue are read in a particular order
  (that's what `ezq.iter_sortq` does).

### Read from the queue using `ezq.iter_msg` or `ezq.iter_sortq`

In the worker, you get the next message by iterating over the queue using
`ezq.iter_msg`. If you need the messages to be read in a sorted order, use `ezq.iter_sortq`.
In both cases, when the special `END` message is reached, the `for` loop will automatically
break (your worker never sees this message).

### End the queue with `ezq.endq` or `ezq.endq_and_wait`

If a queue is not ended, `ezq.iter_msg` (and `ezq.iter_sortq`) will loop forever waiting
for the next message. Therefore, you need to end the queue with one of the two functions
provided.

- `ezq.endq` simply adds the special message to the end of the queue. You can now iterate
  over the queue (e.g., using `ezq.iter_msg`).

- `ezq.endq_and_wait` will put the message in the queue several times-- once for each
  process that you're waiting for. Then it will wait for all the processes to finish before
  returning.

## Example: Read and Write Queues

In this example, several workers read from a queue, process data, and then write to a
different queue that a single worker uses to print to the screen sorting the results as
it goes along. When interfacing with a single I/O device (e.g., screen, file) we typically use a single worker to avoid clashes or overwriting.

```python
import ezq


def printer(write_q):
    """Print results in increasing order."""
    for msg in ezq.iter_sortq(write_q):
        print(msg.data)


def collatz(read_q, write_q):
    """Read numbers and compute values."""
    for msg in ezq.iter_msg(read_q):
        num = msg.data
        if msg.kind == "EVEN":
            write_q.put(ezq.Msg(data=(num, num / 2), order=msg.order))
        elif msg.kind == "ODD":
            write_q.put(ezq.Msg(data=(num, 3 * num + 1), order=msg.order))


def main():
    """Run several subprocesses."""
    read_q, write_q = ezq.Queue(), ezq.Queue()
    readers = [ezq.run(collatz, read_q, write_q) for _ in range(ezq.NUM_CPUS - 1)]
    writers = ezq.run(printer, write_q)

    for i in range(40):
        kind = "EVEN" if i % 2 == 0 else "ODD"
        read_q.put(ezq.Msg(kind=kind, data=i, order=i))

    ezq.endq_and_wait(read_q, readers)
    ezq.endq_and_wait(write_q, writers)


if __name__ == "__main__":
    main()
```

## License

[MIT License](https://github.com/metaist/ezq/blob/main/LICENSE.md)
