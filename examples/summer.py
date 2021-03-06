#!/usr/bin/env python
# coding: utf-8
"""Example of a worker that sums up messages."""
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
