# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog] and this project adheres to [Semantic Versioning].

[keep a changelog]: http://keepachangelog.com/en/1.0.0/
[semantic versioning]: http://semver.org/spec/v2.0.0.html

---

## [2.0.0] - 2021-08-22T19:56:48Z

**Removed**

- `IS_ALIVE`, `stop_iter_msg()`: Originally, these were to stop `iter_msg()` from continuing when there was a `SIGINT`. However, this didn't really work properly and so was removed.
- `Daemon`, `start_processes()`, `start()`, `start_numbered()`: these have all been replaced with a simpler `run()` function.

**Changed**

- `iter_msg()` no longer checks against a global `IS_ALIVE` boolean. It runs until the queue is ended or the process is killed (possibly throwing errors).
- `wait()` is now called `endq_and_wait` to more clearly explain its function.

**Added**

- `iter_sortq()`: iterates over the contents of a queue in a sorted way. Useful for collating results in a single process at the end of a pipeline.
- `endq()`: adds the special `END_MSG` to the queue. This makes the API cleaner in terms of ending queues that don't require waiting.

**Updated**

- README with more examples and key concepts.

[2.0.0]: https://github.com/metaist/ezq/tags/2.0.0

## [1.0.0] - 2021-08-20T19:50Z

Initial release.

[1.0.0]: https://github.com/metaist/ezq/commits/1.0.0
