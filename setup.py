#!/usr/bin/env python3

"""Install library package."""

# native
from pathlib import Path
import site
import sys

# lib
from setuptools import setup, find_namespace_packages

# pkg
pkg = {}
here = Path(__file__).parent.resolve()
top = here / "src" / "ezq"
exec((top / "__about__.py").open().read(), pkg)  # pylint: disable=exec-used

# See: https://github.com/pypa/pip/issues/7953
site.ENABLE_USER_SITE = "--user" in sys.argv[1:]

# See: https://github.com/pypa/pipenv/issues/1911
# See: https://caremad.io/posts/2013/07/setup-vs-requirement/

setup(
    python_requires=">=3.8",
    name="ezq",
    version=pkg["__version__"],
    description=pkg["__doc__"].split("\n")[0],
    long_description=(here / "README.md").read_text(),
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
        "Natural Language :: English",
        "Operating System :: OS Independent",
    ],
)
