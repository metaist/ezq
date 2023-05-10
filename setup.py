#!/usr/bin/env python3

"""Install library package."""

# native
from pathlib import Path
import site
import sys
from typing import Dict

# lib
from setuptools import setup, find_namespace_packages

# pkg
pkg: Dict[str, str] = {}
here = Path(__file__).parent.resolve()
exec(  # pylint: disable=exec-used
    (here / "src" / "ezq" / "__about__.py").open(encoding="utf-8").read(), pkg
)

# See: https://github.com/pypa/pip/issues/7953
site.ENABLE_USER_SITE = "--user" in sys.argv[1:]

# See: https://github.com/pypa/pipenv/issues/1911
# See: https://caremad.io/posts/2013/07/setup-vs-requirement/

setup(
    python_requires=">=3.8",
    name="ezq",
    version=pkg["__version__"],
    description=pkg["__doc__"].split("\n")[0],
    long_description=(here / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    license=pkg["__license__"],
    author=pkg["__author__"],
    author_email=pkg["__email__"],
    url=pkg["__url__"],
    download_url=pkg["__url__"],
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    install_requires=["setuptools"],
    keywords=["simple", "multiprocessing", "queue", "subprocesses"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
    ],
)
