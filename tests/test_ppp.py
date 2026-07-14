from unittest import mock

import ppp.ppp as ppp


def test_tag_dry_run_performs_no_git_operations(monkeypatch):
    """A dry-run tag must not create or push a git tag."""
    monkeypatch.setattr(ppp, 'get_version', lambda: '0.0.4')
    mock_repo = mock.MagicMock()
    mock_repo.tags = []

    with mock.patch.object(ppp, 'Repo', return_value=mock_repo) as repo_cls:
        result = ppp.tag(dry_run=True)

    assert result is True
    repo_cls.assert_called_once()
    mock_repo.git.tag.assert_not_called()
    mock_repo.git.push.assert_not_called()


def test_tag_non_dry_run_creates_and_pushes_tag(monkeypatch):
    """Without dry-run the tag is created and pushed (proves the dry-run path is what gates it)."""
    monkeypatch.setattr(ppp, 'get_version', lambda: '0.0.4')
    mock_repo = mock.MagicMock()
    mock_repo.tags = []

    with mock.patch.object(ppp, 'Repo', return_value=mock_repo):
        ppp.tag(dry_run=False)

    mock_repo.git.tag.assert_called_once()
    mock_repo.git.push.assert_called_once()


def test_main_tag_command_forwards_flags(monkeypatch):
    """`ppp tag -d` must forward dry_run=True to tag(), never a server name."""
    monkeypatch.setattr(ppp.sys, 'argv', ['ppp', 'tag', '-d'])
    monkeypatch.setattr(ppp, 'lint_dir', lambda: True)

    with mock.patch.object(ppp, 'tag', return_value=True) as mock_tag, \
            mock.patch.object(ppp.sys, 'exit') as mock_exit:
        ppp.main()

    mock_tag.assert_called_once_with(verbose=False, dry_run=True)
    mock_exit.assert_called_once_with(True)
