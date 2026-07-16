"""Tests for the pure-logic functions in ppp.ppp.

These exercise the file/text parsing and .pypirc management helpers without any
network access or a real ~/.pypirc: home and cwd are redirected to pytest's
tmp_path and git.Repo is mocked.
"""

import os
from unittest import mock

import pytest

from ppp import ppp


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Redirect os.path.expanduser('~') to an isolated temp directory."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(os.path, "expanduser", lambda _path: str(home))
    return home


def _write_setup_py(directory, body):
    (directory / "setup.py").write_text(body)


# ---------------------------------------------------------------------------
# get_version
# ---------------------------------------------------------------------------

def test_get_version_reads_version(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_setup_py(tmp_path, "version = '1.2.3'\n")
    assert ppp.get_version() == "1.2.3"


def test_get_version_reads_dunder_version(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_setup_py(tmp_path, "__version__ = '0.4.1'\n")
    assert ppp.get_version() == "0.4.1"


def test_get_version_raises_when_absent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_setup_py(tmp_path, "name = 'nothing here'\n")
    with pytest.raises(ValueError):
        ppp.get_version()


# ---------------------------------------------------------------------------
# lint_dir
# ---------------------------------------------------------------------------

def test_lint_dir_passes_with_all_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for name in ("MANIFEST.in", "setup.py", "setup.cfg"):
        (tmp_path / name).write_text("")
    assert ppp.lint_dir() is True


def test_lint_dir_fails_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for name in ("MANIFEST.in", "setup.py"):  # setup.cfg deliberately absent
        (tmp_path / name).write_text("")
    assert ppp.lint_dir() is False


# ---------------------------------------------------------------------------
# update_pypirc
# ---------------------------------------------------------------------------

def _read_pypirc(home):
    import configparser
    parser = configparser.ConfigParser()
    parser.read(str(home / ".pypirc"))
    return parser


def test_update_pypirc_creates_new_file(fake_home):
    result = ppp.update_pypirc("alice", "secret", "https://example.com", "myserver")

    assert result is True
    assert (fake_home / ".pypirc").exists()

    parser = _read_pypirc(fake_home)
    assert parser.has_section("myserver")
    assert parser.get("myserver", "username") == "alice"
    assert parser.get("myserver", "password") == "secret"
    assert parser.get("myserver", "repository") == "https://example.com"
    assert "myserver" in parser.get("distutils", "index-servers")


def test_update_pypirc_upserts_existing_section(fake_home):
    ppp.update_pypirc("alice", "secret", "https://example.com", "myserver")

    # Change just the username / password / repository on the same server.
    ppp.update_pypirc("bob", "hunter2", "https://new.example.com", "myserver")

    parser = _read_pypirc(fake_home)
    assert parser.get("myserver", "username") == "bob"
    assert parser.get("myserver", "password") == "hunter2"
    assert parser.get("myserver", "repository") == "https://new.example.com"
    # No duplicate server entry was appended.
    servers = [s for s in parser.get("distutils", "index-servers").split("\n") if s.strip()]
    assert servers.count("myserver") == 1


def test_update_pypirc_dry_run_writes_nothing(fake_home):
    # Seed an existing file first.
    ppp.update_pypirc("alice", "secret", "https://example.com", "myserver")
    before = (fake_home / ".pypirc").read_text()

    ppp.update_pypirc("bob", "hunter2", "https://new.example.com", "myserver", dry_run=True)

    assert (fake_home / ".pypirc").read_text() == before


# ---------------------------------------------------------------------------
# list_servers
# ---------------------------------------------------------------------------

def test_list_servers_lists_configured_servers(fake_home, capsys):
    ppp.update_pypirc("alice", "secret", "https://example.com", "prod")
    ppp.update_pypirc("alice", "secret", "https://test.example.com", "testpypi")

    assert ppp.list_servers() is True

    out = capsys.readouterr().out
    assert "prod" in out
    assert "testpypi" in out


def test_list_servers_no_file_verbose_returns_true(fake_home):
    # No .pypirc present; verbose path returns True cleanly.
    assert ppp.list_servers(verbose=True) is True


def test_list_servers_no_file_returns_false(fake_home):
    # No .pypirc present and no distutils section to read.
    assert ppp.list_servers() is False


# ---------------------------------------------------------------------------
# check_tag
# ---------------------------------------------------------------------------

def test_check_tag_creates_and_pushes_tag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_setup_py(tmp_path, "version = '2.0.0'\n")

    fake_repo = mock.Mock()
    fake_repo.tags = []
    with mock.patch.object(ppp, "Repo", return_value=fake_repo) as repo_cls:
        assert ppp.check_tag() is True

    repo_cls.assert_called_once_with(path=os.getcwd())
    fake_repo.git.tag.assert_called_once()
    fake_repo.git.push.assert_called_once_with(tags=True)


def test_check_tag_raises_on_duplicate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_setup_py(tmp_path, "version = '2.0.0'\n")

    fake_repo = mock.Mock()
    fake_repo.tags = ["2.0.0"]  # tag already exists
    with mock.patch.object(ppp, "Repo", return_value=fake_repo):
        with pytest.raises(ValueError):
            ppp.check_tag()

    fake_repo.git.tag.assert_not_called()


def test_check_tag_dry_run_does_not_tag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_setup_py(tmp_path, "version = '2.0.0'\n")

    fake_repo = mock.Mock()
    fake_repo.tags = []
    with mock.patch.object(ppp, "Repo", return_value=fake_repo):
        assert ppp.check_tag(dry_run=True) is True

    fake_repo.git.tag.assert_not_called()
    fake_repo.git.push.assert_not_called()


def test_tag_non_dry_run_creates_and_pushes_tag(monkeypatch):
    """The tag command creates and pushes a tag when not in dry-run mode."""
    monkeypatch.setattr(ppp, "get_version", lambda: "0.0.4")
    fake_repo = mock.MagicMock()
    fake_repo.tags = []

    with mock.patch.object(ppp, "Repo", return_value=fake_repo):
        ppp.tag(dry_run=False)

    fake_repo.git.tag.assert_called_once()
    fake_repo.git.push.assert_called_once()


def test_main_tag_command_forwards_flags(monkeypatch):
    """The tag CLI forwards verbose and dry-run flags to tag()."""
    monkeypatch.setattr(ppp.sys, "argv", ["ppp", "tag", "-d"])
    monkeypatch.setattr(ppp, "lint_dir", lambda: True)

    with mock.patch.object(ppp, "tag", return_value=True) as mock_tag, \
            mock.patch.object(ppp.sys, "exit") as mock_exit:
        ppp.main()

    mock_tag.assert_called_once_with(verbose=False, dry_run=True)
    mock_exit.assert_called_once_with(True)
