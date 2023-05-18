# Contributing

This document describes the process of making a release.

## Checkout `prod`

```bash
git checkout prod
git merge --no-ff --no-edit main
```

## Update `__about__.py`

Get the current UTC date+time:

```bash
python -c"from datetime import datetime; print(datetime.utcnow().isoformat()[:19] + 'Z')"
```

Update `__about__.py` with the correct values:

```python
__version__ = "<<NEW VERSION>>"
__pubdate__ = "<<DATE+TIME IN UTC>>"
```

Take the time to also update the `__copyright__` line, if needed.

Example:

```python
__version__ = "2.0.3"
__pubdate__ = "2023-05-10T03:44:41Z"
```

## Update `CHANGELOG.md`

Sections order is: `Fixed`, `Changed`, `Added`, `Deprecated`, `Removed`, `Security`.

```text
---
[2.0.3]: https://github.com/metaist/ezq/compare/2.0.2...2.0.3

## [2.0.3] - 2023-05-10T03:45:10Z



**Fixed**

**Changed**

**Added**

**Deprecated**

**Removed**

**Security**

```

## Update docs

```bash
pdoc --html --output-dir docs --force src/ezq
mv docs/ezq/* docs/
```

## Check build

```bash
python setup.py build
twine check dist/*
```

## Commit & Push

```bash
git commit -m "release: 2.0.3"
git tag 2.0.3
git push
git push --tags
git checkout main
git merge --no-ff --no-edit prod
git push
```

## Create Release

Visit: https://github.com/metaist/ezq/releases/new
