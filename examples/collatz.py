#!/usr/bin/env python
# coding: utf-8
"""Compute the next Collatz number for numbers 0-39.

NOTE: I know this isn't really the Collatz algorithm.
"""

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
    q, out = ezq.Q(thread=True), ezq.Q()
    readers = [ezq.run_thread(collatz, q, out) for _ in range(ezq.NUM_THREADS)]
    writer = ezq.run(printer, out)

    for num in range(40):
        kind = "EVEN" if num % 2 == 0 else "ODD"
        q.put(num, kind=kind, order=num)

    q.stop(readers)
    out.stop(writer)


if __name__ == "__main__":
    main()
