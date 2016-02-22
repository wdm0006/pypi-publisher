"""
.. module:: ppp
   :platform: Unix, Windows
   :synopsis: A module for publishing pypi packages to public and private servers

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

import os
import sys
import uuid
import configparser
import argparse

__author__ = 'willmcginnis'


def lint_dir():
    """
    Checks the directory for appropriate files (like a manifest and setup.cfg, etc).

    :return:
    """

    return True


def update_pypirc(username, password, index_url, server_name, verbose=False, dry_run=False):
    """
    Upserts into the pypirc file with new information from the command line.

    :param username:
    :param password:
    :param index_url:
    :param server_name:
    :return:
    """

    if verbose:
        print('Updating pypirc file')
        print('\tsearching for pypirc file...')

    f_path = os.path.join(os.path.expanduser('~'), '.pypirc')
    if os.path.exists(f_path):
        if verbose:
            print('\tpypirc file found.')
    else:
        if verbose:
            print('\tNo pypirc file found, creating a new one')

        seed_parser = configparser.ConfigParser()
        seed_parser.add_section('distutils')
        seed_parser.set(section='distutils', option='index-servers', value='')

        if not dry_run:
            with open(f_path, 'w') as f:
                seed_parser.write(f)

    parser = configparser.ConfigParser()
    parser.read(f_path)
    if parser.has_section(server_name):
        if verbose:
            print('\tserver name already exists')
        if username != parser.get(section=server_name, option='username'):
            if verbose:
                print('\tupdating username')
            parser.set(section=server_name, option='username', value=username)
        if password != parser.get(section=server_name, option='password'):
            if verbose:
                print('\tupdating password')
            parser.set(section=server_name, option='password', value=password)
        if index_url != parser.get(section=server_name, option='repository'):
            if verbose:
                print('\tupdating index url')
            parser.set(section=server_name, option='repository', value=index_url)
    else:
        if verbose:
            print('\tserver name not there, adding it...')
        parser.add_section(server_name)
        index_servers = parser.get(section='distutils', option='index-servers') + '\n%s' % (server_name, )
        parser.set(section='distutils', option='index-servers', value=index_servers)
        parser.set(section=server_name, option='repository', value=index_url)
        parser.set(section=server_name, option='username', value=username)
        parser.set(section=server_name, option='password', value=password)

    if not dry_run:
        with open(f_path, 'w') as f:
            parser.write(f)

    return True


def publish(server_name, verbose=False, dry_run=False):
    """

    :param verbose:
    :return:
    """

    executable = sys.executable

    if verbose:
        print('registering...')

    cmd = '%s setup.py register -r %s' % (executable, server_name, )
    if dry_run:
        print(cmd)
    else:
        os.system(cmd)

    if verbose:
        print('publishing....')

    cmd = '%s setup.py sdist upload -r %s' % (executable, server_name, )
    if dry_run:
        print(cmd)
    else:
        os.system(cmd)

    return True


def main():
    """

    :return:
    """

    # Setup an argument parser
    parser = argparse.ArgumentParser(description='PyPI Publisher: CLI for publishing projects to PyPI')

    # add the various arguments
    parser.add_argument('command')
    parser.add_argument('-u', '--username', dest='username', help='')
    parser.add_argument('-p', '--password', dest='password', help='')
    parser.add_argument('-i', '--index-url', dest='index_url', help='')
    parser.add_argument('-s', '--server-name', dest='server_name', help='')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='log out verbose information')
    parser.add_argument('-d', '--dry-run', action='store_true', dest='dry_run', help='dry run (just log out the commands')

    # parse them out
    args = parser.parse_args()
    verbose = args.verbose
    command = args.command
    server_name = args.server_name
    password = args.password
    username = args.username
    index_url = args.index_url
    dry_run = args.dry_run

    # if server name is null use a uuid
    if server_name is None:
        server_name = str(uuid.uuid4())

    # get the values from the on-disk pypirc file if needed
    update_pypirc(username, password, index_url, server_name, verbose=verbose, dry_run=dry_run)

    if command.lower() == 'publish':
        clean = lint_dir()
        if clean:
            return sys.exit(publish(server_name, verbose=verbose, dry_run=dry_run))
        else:
            raise ValueError('Directory Linting Failed.')
    else:
        raise NotImplementedError('Command %s not recognized' % (command, ))


if __name__ == '__main__':
    main()