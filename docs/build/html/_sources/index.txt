.. ppp documentation master file, created by
   sphinx-quickstart on Tue Mar  1 19:19:00 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

PyPI-Publisher (ppp)
====================

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

.. code-block::none

    pip install pypi-publisher


Or clone the repo:

.. code-block:: none

    git clone https://github.com/wdm0006/pypi-publisher.git
    python setup.py install

Then to use just:

.. code-block:: none

    ppp [command] [-options]

Available commands are:

 * publish
 * tag
 * publish-sphinx
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

Updating .pypi file
^^^^^^^^^^^^^^^^^^^

If you already have a .pypi file at ~ on the box, then you can just pass -s to reference a server in that.  If you pass
-s and -u, -p, and/or -i for a server that is in the file already, the parameters passed will be upserted into that
file.  If you pass -s, -u, -p, and -i for a server that is not in the file, it will be inserted as a new server.

A few examples:

To use an existing server

.. code-block:: none

    ppp publish -s=foo

To update some values (username and index url) for an existing server

.. code-block:: none

    ppp publish -s=foo -u=bar -i=baz

To create a whole new server:

.. code-block:: none

    ppp publish -s=foo -u=bar -p=baz -i=bat

Linting the candidate repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Currently, the linting is very basic, and is just checking that a few files actually exist (manifest.in, setup.py and
setup.cfg).  This happens in all runs, regardless of flags passed.

Pushing a tag to git
^^^^^^^^^^^^^^^^^^^^

If you pass the -t flag, ppp will try to find the version number in the setup.py file and push a tag with the version to
git.  The search looks for any line (case insensitive) that starts with __version__ or version, and takes it's value, so

.. code-block:: python

    __version__ = '1.0.0'



or

.. code-block:: python

    VERSION = '1.0.0'

Would both work perfectly. It's worth noting that if you push tags on the initial publishing to a test server, you won't
need to push the same tag again for the following publishing to the prod server.

Publishing the repository
^^^^^^^^^^^^^^^^^^^^^^^^^

Currently, this only supports sdist uploads, in the future we plan to add more sophisticated packaging functionality,
like wheels.


Detailed Documentation
======================

Coming soon.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

