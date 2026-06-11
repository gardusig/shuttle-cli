"""Verify scripts/git wrappers exist and have valid syntax."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT_SCRIPTS = ROOT / "scripts" / "git"


def test_all_cursor_skills_git_scripts_exist() -> None:
    expected = {
        "branch.sh",
        "branch-delete.sh",
        "branch-delete-all.sh",
        "branch-clear.sh",
        "cherry-pick.sh",
        "commit.sh",
        "docs.sh",
        "large-files.sh",
        "main.sh",
        "post-merge-cleanup.sh",
        "pull.sh",
        "push.sh",
        "rebase.sh",
        "reset.sh",
        "revert.sh",
        "review.sh",
        "start.sh",
        "stash.sh",
        "tag.sh",
        "zip.sh",
    }
    found = {p.name for p in GIT_SCRIPTS.glob("*.sh") if p.name != "_common.sh"}
    assert found == expected
