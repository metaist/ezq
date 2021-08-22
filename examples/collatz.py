#!/usr/bin/env python
# coding: utf-8
"""Example of ezq using collatz conjecture-like work.

Note this example doesn't actually do anything useful. It's for illustrative purposes only.
"""

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
