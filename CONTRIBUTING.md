# Contributing

This document describes the process of making a release.

## Checkout `prod`

```bash
git checkout prod
git merge --no-ff --no-edit main
```

## Update `pyproject.toml`

Update:

```toml
version = "3.0.1"
```

## Update `CHANGELOG.md`

Sections order is: `Fixed`, `Changed`, `Added`, `Deprecated`, `Removed`, `Security`.

```text
---
[3.0.1]: https://github.com/metaist/ezq/compare/3.0.0...3.0.1

## [3.0.1] - 2023-05-22T00:39:34Z

**Fixed**

**Changed**

**Added**

**Deprecated**

**Removed**

**Security**

```

## Update docs

```bash
pdoc --html --output-dir docs --force src/$(basename $(pwd))
mv docs/*/* docs/
```

## Check build

```bash
python -c "from setuptools import setup; setup()" build
```

## Commit & Push

```bash
git commit -am "release: 3.0.1"
git tag 3.0.1
git push
git push --tags
git checkout main
git merge --no-ff --no-edit prod
git push
```

## Create Release

Visit: https://github.com/metaist/ezq/releases/new
