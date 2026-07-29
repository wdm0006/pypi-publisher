pypi-publisher (ppp)
====================

> **This project is archived and is no longer maintained.**
>
> `ppp` was written in 2016 to combine `.pypirc` management, a directory check, git tagging and a
> `setup.py` upload into one command. All of those steps are now covered by maintained tools, and
> its central feature — storing an index username and password in `~/.pypirc` — has been superseded
> by PyPI Trusted Publishing, which issues short-lived tokens instead. `ppp` also only works on
> legacy `setup.py` projects and cannot read a version from `pyproject.toml`.
>
> The full 2026 assessment behind this decision is in
> [pull request #20](https://github.com/wdm0006/pypi-publisher/pull/20).
>
> The repository stays public and read-only. Version 0.0.4 remains installable from PyPI; it will
> not be yanked, since it is not broken so much as obsolete.

What to use instead
-------------------

Replace `ppp publish` with two commands and one decision:

 1. **Build** with `uv build` (or `python -m build`, `hatch build`, `flit build` — any of them
    produce `dist/`).
 2. **Upload** either with `twine upload -r <server> dist/*`, which reads the same `~/.pypirc` that
    `ppp` was writing, so existing server sections keep working — or, better, configure a
    [PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/) and let
    [`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish) upload from a
    tagged CI run, so no upload credential is stored anywhere.

For tagging, use `git tag` / `gh release create` directly, or adopt
[`python-semantic-release`](https://python-semantic-release.readthedocs.io/) if you want the version
bump, changelog and tag derived from commit messages.

---

The original README follows, for reference.

---

author: Will McGinnis

[![PyPI Version](http://badge.kloud51.com/pypi/v/pypi-publisher.svg)](https://pypi.python.org/pypi/pypi-publisher)
[![PyPI Status](http://badge.kloud51.com/pypi/s/pypi-publisher.svg)](https://pypi.python.org/pypi/pypi-publisher)
[![PyPI License](http://badge.kloud51.com/pypi/l/pypi-publisher.svg)](https://pypi.python.org/pypi/pypi-publisher)
[![PyPI Wheel](http://badge.kloud51.com/pypi/w/pypi-publisher.svg)](https://pypi.python.org/pypi/pypi-publisher)
[![PyPI Format](http://badge.kloud51.com/pypi/f/pypi-publisher.svg)](https://pypi.python.org/pypi/pypi-publisher)
[![PyPI Py_versions](http://badge.kloud51.com/pypi/p/pypi-publisher.svg)](https://pypi.python.org/pypi/pypi-publisher)
[![PyPI Downloads](http://badge.kloud51.com/pypi/d/pypi-publisher.svg)](https://pypi.python.org/pypi/pypi-publisher)
[![PyPI Implementation](http://badge.kloud51.com/pypi/i/pypi-publisher.svg)](https://pypi.python.org/pypi/pypi-publisher)
[![PyPI Egg](http://badge.kloud51.com/pypi/e/pypi-publisher.svg)](https://pypi.python.org/pypi/pypi-publisher)

Overview
--------

A cli for publishing packages to pypi, without the hassle. It just lets you in one command line call upsert into your 
.pypirc file (or reference a server already in it, or create a new file altogether if it doesn't exist), create the git
tag for the version specified in your setup.py file, lint the directory to make sure the required files are there, then 
register and push it all up.

Super easy.

In the future, we aim to add in more complex linting / last minute checks and aim to remove the need for a pypirc file 
in the first place (perhaps by creating it on the the fly with the passed args and removing it, or by mocking it).

Installation / Usage
--------------------

To install use pip:

    $ pip install pypi-publisher


Or clone the repo:

    $ git clone https://github.com/wdm0006/pypi-publisher.git
    $ python setup.py install
    
Then to use just:

    $ ppp [command] [-options]

Available commands are:

 * publish
 * tag
 * list-servers
 
Available options are:

 * -u/--username
 * -p/--password
 * -i/--index-url
 * -s/--server-name
 * -d/--dry-run
 * -v/--verbose
 * -t/--create-tag

In general, the 4 things being done are:

 1. update the .pypi file
 2. linting the candidate repository
 3. pushing a tag to git for the release
 4. publishing the repository to a pypi server
 
### Updating .pypi file

If you already have a .pypi file at ~ on the box, then you can just pass -s to reference a server in that.  If you pass
-s and -u, -p, and/or -i for a server that is in the file already, the parameters passed will be upserted into that 
file.  If you pass -s, -u, -p, and -i for a server that is not in the file, it will be inserted as a new server.

A few examples:

To use an existing server

    ppp publish -s=foo
    
To update some values (username and index url) for an existing server

    ppp publish -s=foo -u=bar -i=baz
    
To create a whole new server:

    ppp publish -s=foo -u=bar -p=baz -i=bat

### Linting the candidate repository

Currently, the linting is very basic, and is just checking that a few files actually exist (manifest.in, setup.py and 
setup.cfg).  This happens in all runs, regardless of flags passed.

### Pushing a tag to git

If you pass the -t flag, ppp will try to find the version number in the setup.py file and push a tag with the version to
git.  The search looks for any line (case insensitive) that starts with __version__ or version, and takes it's value, so

    __version__ = '1.0.0'

or 

    VERSION = '1.0.0'
    
Would both work perfectly. It's worth noting that if you push tags on the initial publishing to a test server, you won't 
need to push the same tag again for the following publishing to the prod server.

### Publishing the repository 

Currently, this only supports sdist uploads, in the future we plan to add more sophisticated packaging functionality, 
like wheels.

Contributing
------------

The repository is archived and read-only: issues and pull requests are closed. See the archive
notice at the top for what to use instead. 
