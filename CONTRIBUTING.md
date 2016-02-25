Contributing
============

Things I'd like to add in and would love help with:

 * Add a command for tag, which just lints and tags, and doesn't do the upload to pypi
 * Support for different things than sdist, notably wheels
 * More sophisticated linting (making sure the right things are in manifest, based on what is used in setup, perhaps)
 * A testing command for attempting to install a package from the test pypi server after upload
 * Full workflow, so a single action to:
    * tag
    * push to test
    * verify successful packaging from test 
    * push to prod