pypi-publisher (ppp)
====================

version number: 0.0.2
author: Will McGinnis

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

    $ pip install ppp


Or clone the repo:

    $ git clone https://github.com/wdm0006/ppp.git
    $ python setup.py install
    
Then to use just:

    $ ppp publish [-options]

Available options are:

 * -u/--username
 * -p/--password
 * -i/--index-url
 * -s/--server-name
 * -d/--dry-run
 * -v/--verbose
 * -t/--create-tag

Contributing
------------

If you run into trouble, please let me know, open an issue or shoot me a pull request. 