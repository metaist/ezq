#!/usr/bin/env python
"""Example of using a mixture of processes and threads."""

# pkg
import ezq


def worker_thread(q: ezq.Q, out: ezq.Q) -> None:
    """Compute numeric value of each letter."""
    for msg in q:
        out.put(ord(msg.data))


def worker_process(q: ezq.Q, out: ezq.Q) -> None:
    """Break a word apart into letters."""
    q2 = ezq.Q(thread=True)
    threads = [ezq.run_thread(worker_thread, q2, out) for _ in range(10)]
    for msg in q:
        for letter in msg.data:
            q2.put(letter)
    q2.stop(threads)


def main() -> None:
    """Process a block of text and compute the sum of all ASCII letters."""
    q, out = ezq.Q(), ezq.Q()
    workers = [ezq.run(worker_process, q, out) for _ in range(ezq.NUM_CPUS)]

    data = """
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam in semper
        tortor, ac maximus magna. Sed quis rhoncus nulla. Vestibulum at felis dolor.
        Morbi quis odio ut lorem molestie viverra sed nec augue. Pellentesque
        vestibulum sollicitudin euismod. Vivamus ullamcorper justo at erat hendrerit,
        vitae blandit erat imperdiet. Proin faucibus nisl non sem finibus tristique.
        Nunc scelerisque, felis ac consequat auctor, ligula orci placerat dui, sed
        ultricies risus ligula convallis risus. Cras volutpat ipsum neque, nec finibus
        lacus interdum vitae. Aliquam erat volutpat.
    """
    for word in data.split(" "):
        q.put(word)
    q.stop(workers)

    print(sum(msg.data for msg in out.items()))


if __name__ == "__main__":
    main()
