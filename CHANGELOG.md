# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog] and this project adheres to [Semantic Versioning].

Sections order is: `Fixed`, `Changed`, `Added`, `Deprecated`, `Removed`, `Security`.

[keep a changelog]: http://keepachangelog.com/en/1.0.0/
[semantic versioning]: http://semver.org/spec/v2.0.0.html

---

[unreleased]: https://github.com/metaist/ezq/compare/prod...main

## [Unreleased]

These are changes that are on `main` that are not yet in `prod`.

---

[#5]: https://github.com/metaist/ezq/issues/5
[#7]: https://github.com/metaist/ezq/issues/7
[#8]: https://github.com/metaist/ezq/issues/8
[#9]: https://github.com/metaist/ezq/issues/9
[3.0.0]: https://github.com/metaist/ezq/compare/2.0.3...3.0.0

## [3.0.0] - 2023-05-18T09:58:43Z

**Fixed**

- GitHub Action: continuous integration
- [#9]: `multiprocessing` on MacOS (by switching to `multiprocess`)

**Changed**

- [#8]: order of `Msg` parameters so that `data` comes first
- [#9]: core library is now `multiprocess` instead of `multiprocessing`; `dill` replaces `pickle`.

**Added**

- GitHub Action: `mypy` check for examples and tests
- supported python versions badge
- [#5]: `Worker` wrapper for `Process` and `Thread`
- `cSpell` to track ignored words

**Removed**

- [#7]: deprecated functions: `put_msg`, `iter_msg`, `iter_q`, `sortiter`, `endq`, `endq_and_wait`

---

[#1]: https://github.com/metaist/ezq/issues/1
[#3]: https://github.com/metaist/ezq/issues/3
[#4]: https://github.com/metaist/ezq/issues/4
[#6]: https://github.com/metaist/ezq/issues/6
[2.0.3]: https://github.com/metaist/ezq/compare/2.0.2...2.0.3

## [2.0.3] - 2023-05-10T03:44:15Z

This version introduced a new class-based API via the `Q` object.
The function-based API is officially deprecated and will be removed
in v3.

**Changed**

- `sortiter` now sorts the list of waiting messages in place to improve performance (~50%).
- replaced `pylint` with [`ruff`](https://github.com/charliermarsh/ruff)
- [#6]: supported python versions: removed 3.6, 3.7; added 3.10, 3.11

**Added**

- build badge
- [#1]: support for `threading`
- [#3]: `map` function for simple use-cases
- [#4]: `Q` class wrapper for the queue

**Deprecated**

Most of the function-based API is now deprecated.

- `put_msg`: use `Q.put()` instead
- `iter_msg`: use `iter(Q)` instead
- `iter_q`: use `Q.items()` instead
- `sortiter`: use `Q.sorted()` instead
- `endq`: use `Q.end()` instead
- `endq_and_wait`: use `Q.stop()` instead

---

[2.0.2]: https://github.com/metaist/ezq/compare/2.0.1...2.0.2

## [2.0.2] - 2021-08-24T17:25:52Z

**Changed**

- `iter_msg` to handle `block` parameter
- `iter_sortq` to be a more generic `sortiter`

**Added**

- [Documentation](https://metaist.github.io/ezq)
- `sortiter` which is a more general form of `iter_sortq`
- `iter_q` for iterating over current contents of a queue

**Removed**

- `count` parameter for `endq`; it was only used internally and was confusing

---

[2.0.1]: https://github.com/metaist/ezq/compare/2.0.0...2.0.1

## [2.0.1] - 2021-08-22T20:20:53Z

**Fixed**

- README link to license.
- `setup.py` to contain a better `long_description`.

---

[2.0.0]: https://github.com/metaist/ezq/compare/1.0.0...2.0.0

## [2.0.0] - 2021-08-22T19:56:48Z

**Changed**

- `iter_msg()` no longer checks against a global `IS_ALIVE` boolean. It runs until the queue is ended or the process is killed (possibly throwing errors).
- `wait()` is now called `endq_and_wait` to more clearly explain its function.
- README with more examples and key concepts.

**Added**

- `iter_sortq()`: iterates over the contents of a queue in a sorted way. Useful for collating results in a single process at the end of a pipeline.
- `endq()`: adds the special `END_MSG` to the queue. This makes the API cleaner in terms of ending queues that don't require waiting.

**Removed**

- `IS_ALIVE`, `stop_iter_msg()`: Originally, these were to stop `iter_msg()` from continuing when there was a `SIGINT`. However, this didn't really work properly and so was removed.
- `Daemon`, `start_processes()`, `start()`, `start_numbered()`: these have all been replaced with a simpler `run()` function.

---

[1.0.0]: https://github.com/metaist/ezq/commits/1.0.0

## [1.0.0] - 2021-08-20T19:50Z

Initial release.
