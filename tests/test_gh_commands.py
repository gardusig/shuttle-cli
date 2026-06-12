"""Unit tests for shuttle gh commands and services."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.services.gh_sequence import SequenceKey, sort_issues_by_sequence

runner = CliRunner()


@pytest.fixture
def mock_svc() -> MagicMock:
    svc = MagicMock()
    svc.repo_display.return_value = "owner/repo"
    svc.snapshot_summary.return_value = ["repo: owner/repo"]
    return svc


def test_sequence_key_from_title() -> None:
    assert SequenceKey.from_title("1 — Epic foo") == SequenceKey(1, None)
    assert SequenceKey.from_title("1.2 — Child bar") == SequenceKey(1, 2)
    assert SequenceKey.from_title("no prefix") is None


def test_sort_issues_by_sequence() -> None:
    issues = [
        {"number": 3, "title": "2 — Second"},
        {"number": 1, "title": "1.2 — Child"},
        {"number": 2, "title": "1 — Epic"},
    ]
    ordered = sort_issues_by_sequence(issues)
    assert [i["number"] for i in ordered] == [2, 1, 3]


@patch("shuttle.commands.gh._svc")
def test_issue_list_json(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.issue_list.return_value = [{"number": 1, "title": "1 — Epic"}]
    result = runner.invoke(app, ["gh", "--format", "json", "issue", "list"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data[0]["number"] == 1


@patch("shuttle.commands.gh._svc")
def test_issue_create_requires_yes_in_non_tty(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    result = runner.invoke(
        app,
        ["gh", "issue", "create", "--title", "Test"],
    )
    assert result.exit_code != 0
    assert "non-interactive" in result.output.lower() or result.exit_code == 1


@patch("shuttle.commands.gh._svc")
def test_issue_create_with_yes(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.issue_create.return_value = {"number": 42, "title": "Test", "url": "https://x/42"}
    result = runner.invoke(
        app,
        ["gh", "issue", "create", "--title", "Test", "--yes"],
    )
    assert result.exit_code == 0
    mock_svc.issue_create.assert_called_once()


@patch("shuttle.commands.gh._svc")
def test_backlog_next(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.backlog_next.return_value = {"number": 5, "title": "1.1 — Child", "sequence": "1.1 —"}
    result = runner.invoke(app, ["gh", "--format", "json", "backlog", "next"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["number"] == 5


@patch("shuttle.commands.gh._svc")
def test_label_sync_with_yes(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.label_sync.return_value = {"created": ["epic:test"], "deleted": []}
    result = runner.invoke(
        app,
        ["gh", "label", "sync", "--manifest", "labels.yaml", "--yes"],
    )
    assert result.exit_code == 0


def test_gh_help() -> None:
    result = runner.invoke(app, ["gh", "--help"])
    assert result.exit_code == 0
    assert "issue" in result.output


@patch("shuttle.commands.gh._svc")
def test_repo_view_json(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.repo_view.return_value = {"nameWithOwner": "owner/repo", "owner": {"login": "owner"}}
    result = runner.invoke(
        app,
        ["gh", "--format", "json", "repo", "view", "--json-fields", "nameWithOwner,owner"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["nameWithOwner"] == "owner/repo"
    mock_svc.repo_view.assert_called_once_with(fields="nameWithOwner,owner")


@patch("shuttle.commands.gh._svc")
def test_pr_list_head_base_filters(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.pr_list.return_value = [{"number": 1, "title": "PR"}]
    result = runner.invoke(
        app,
        ["gh", "--format", "json", "pr", "list", "--head", "feature", "--base", "main"],
    )
    assert result.exit_code == 0
    mock_svc.pr_list.assert_called_once_with(state="open", limit=30, head="feature", base="main")
