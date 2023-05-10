#!/usr/bin/env python
# coding: utf-8
"""Example of a worker that sums up messages."""

import ezq


def worker(q: ezq.Q, out: ezq.Q) -> None:
    """Add up all the messages."""
    total = 0
    for msg in q:  # read a message from the queue
        total += msg.data

    # after reading all the messages, write the total
    out.put(total)


def main() -> None:
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
