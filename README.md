# ezq - Simple wrappers for python multiprocessing

## Purpose

An easy way to get started using queues and multiprocessing in python.

## Install

```bash
pip install ezq
```

## Quick Start

The general idea is that you connect subprocesses (workers) with queues.

Here's a simple example of a worker that just sums up the messages.

```python
from functools import partial
import ezq


def worker(q):
    """Add up all the messges."""
    count = sum(msg.data for msg in ezq.iter_msg(q))
    # do something with count


def main():
    """Run many workers."""
    q = ezq.Queue()
    workers = ezq.start(partial(worker, q))
    for i in range(1000):
        q.put(ezq.Msg(data=i))

    ezq.wait(q, workers)

if __name__ == "__main__":
    main()
```
