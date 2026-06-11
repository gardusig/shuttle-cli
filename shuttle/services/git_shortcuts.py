from __future__ import annotations

import time
from pathlib import Path

from shuttle.utils.process import GitCommandError, run_git


class GitShortcuts:
    """Local git operations with safety gates for destructive actions."""

    def __init__(self, top: str | None = None) -> None:
        self.top = top or self.repo_root()

    @staticmethod
    def repo_root() -> str:
        return run_git(["rev-parse", "--show-toplevel"]).stdout.strip()

    def current_branch(self) -> str:
        return run_git(["branch", "--show-current"], cwd=self.top).stdout.strip()

    def status_short(self) -> str:
        return run_git(["status", "--short"], cwd=self.top).stdout

    def is_dirty(self) -> bool:
        return bool(self.status_short().strip())

    def has_upstream(self) -> bool:
        result = run_git(
            ["rev-parse", "--abbrev-ref", "@{u}"],
            cwd=self.top,
            check=False,
        )
        return result.returncode == 0

    def remote_exists(self, name: str = "origin") -> bool:
        result = run_git(["remote", "get-url", name], cwd=self.top, check=False)
        return result.returncode == 0

    def canonical_main_ref(self) -> str:
        if self.remote_exists("upstream"):
            return "upstream/main"
        return "origin/main"

    def fetch_all(self, *, prune: bool = False) -> None:
        args = ["fetch", "origin"]
        if prune:
            args.append("--prune")
        run_git(args, cwd=self.top)
        if self.remote_exists("upstream"):
            up_args = ["fetch", "upstream"]
            if prune:
                up_args.append("--prune")
            run_git(up_args, cwd=self.top)

    def checkout_main(self) -> None:
        result = run_git(["checkout", "main"], cwd=self.top, check=False)
        if result.returncode != 0:
            if self.remote_exists("origin"):
                run_git(["checkout", "-B", "main", "origin/main"], cwd=self.top)
            else:
                raise GitCommandError(
                    ["git", "checkout", "main"],
                    result.returncode,
                    result.stderr,
                )

    def align_main(self, *, yes: bool = False, keep_ignored: bool = False) -> None:
        if self.is_dirty() and not yes:
            raise RuntimeError(
                "Working tree is dirty. Re-run with --yes to discard local changes."
            )
        self.checkout_main()
        self.fetch_all()
        ref = self.canonical_main_ref()
        run_git(["rev-parse", ref], cwd=self.top)
        run_git(["reset", "--hard", ref], cwd=self.top)
        clean_args = ["clean", "-fd"] if keep_ignored else ["clean", "-fdx"]
        run_git(clean_args, cwd=self.top)

    def commit(self, message: str = ".", *, paths: list[str] | None = None) -> bool:
        if paths:
            run_git(["add", "--", *paths], cwd=self.top)
        else:
            run_git(["add", "-A"], cwd=self.top)
        staged = run_git(["diff", "--cached", "--quiet"], cwd=self.top, check=False)
        if staged.returncode == 0:
            return False
        run_git(["commit", "-m", message], cwd=self.top)
        return True

    def push(self, *, allow_main: bool = False, message: str = ".", yes: bool = False) -> None:
        if not yes:
            raise RuntimeError("Push requires confirmation. Pass --yes to proceed.")
        branch = self.current_branch()
        if branch == "main" and not allow_main:
            raise RuntimeError(
                "Refusing to push main. Create a feature branch or pass --allow-main."
            )
        if self.is_dirty():
            self.commit(message)
        if not self.remote_exists("origin"):
            raise RuntimeError("No origin remote configured.")
        run_git(["push", "-u", "origin", "HEAD"], cwd=self.top)

    def pull(self, *, merge_branch: str | None = None) -> None:
        self.fetch_all()
        if self.has_upstream():
            run_git(["merge", "@{u}"], cwd=self.top)
        root = self.canonical_main_ref()
        run_git(["rev-parse", root], cwd=self.top)
        if merge_branch:
            run_git(["merge", merge_branch], cwd=self.top)
        elif self.current_branch() != "main":
            run_git(["merge", root], cwd=self.top)

    def start(
        self,
        branch: str | None = None,
        *,
        align_main: bool = False,
        yes: bool = False,
        no_push: bool = True,
        message: str = ".",
    ) -> str:
        """Create a branch from current state. Main alignment is opt-in only."""
        if align_main:
            self.align_main(yes=yes)
        name = branch or f"wip-{int(time.time())}"
        run_git(["checkout", "-b", name], cwd=self.top)
        if not no_push:
            self.push(message=message, yes=yes)
        return name

    def stash_push(self, message: str | None = None) -> None:
        args = ["stash", "push"]
        if message:
            args.extend(["-m", message])
        run_git(args, cwd=self.top)

    def stash_list(self) -> str:
        return run_git(["stash", "list"], cwd=self.top).stdout

    def stash_apply(self, index: int = 0) -> None:
        run_git(["stash", "apply", f"stash@{{{index}}}"], cwd=self.top)

    def stash_pop(self, index: int = 0) -> None:
        run_git(["stash", "pop", f"stash@{{{index}}}"], cwd=self.top)

    def stash_drop(self, index: int = 0, *, yes: bool = False) -> None:
        if not yes:
            raise RuntimeError("Pass --yes to drop a stash entry.")
        run_git(["stash", "drop", f"stash@{{{index}}}"], cwd=self.top)

    def stash_clear(self, *, yes: bool = False) -> None:
        if not yes:
            raise RuntimeError("Pass --yes to clear all stashes.")
        run_git(["stash", "clear"], cwd=self.top)

    def branch_list(self) -> str:
        return run_git(["branch", "-a", "-vv"], cwd=self.top).stdout

    def branch_prune(self) -> None:
        self.fetch_all(prune=True)

    def branch_delete(
        self,
        name: str,
        *,
        force: bool = False,
        remote: bool = True,
        yes: bool = False,
    ) -> None:
        if not yes:
            raise RuntimeError("Pass --yes to delete a branch.")
        current = self.current_branch()
        if name == current:
            raise RuntimeError(f"Cannot delete current branch: {name}")
        flag = "-D" if force else "-d"
        run_git(["branch", flag, name], cwd=self.top)
        if remote and self.remote_exists("origin"):
            run_git(["push", "origin", "--delete", name], cwd=self.top, check=False)

    def branch_delete_all_merged(self, *, yes: bool = False) -> list[str]:
        if not yes:
            raise RuntimeError("Pass --yes to delete merged branches.")
        self.branch_prune()
        current = self.current_branch()
        protected = {"main", current}
        out = run_git(["branch", "--merged"], cwd=self.top).stdout
        deleted: list[str] = []
        for line in out.splitlines():
            name = line.strip().lstrip("* ").strip()
            if not name or name in protected:
                continue
            self.branch_delete(name, force=False, remote=True, yes=True)
            deleted.append(name)
        return deleted

    def post_merge_cleanup(self, *, yes: bool = False) -> list[str]:
        self.align_main(yes=yes)
        return self.branch_delete_all_merged(yes=yes)

    def rebase(
        self,
        onto: str | None = None,
        *,
        continue_: bool = False,
        abort: bool = False,
    ) -> None:
        if abort:
            run_git(["rebase", "--abort"], cwd=self.top)
            return
        if continue_:
            run_git(["rebase", "--continue"], cwd=self.top)
            return
        target = onto or self.canonical_main_ref()
        self.fetch_all()
        run_git(["rebase", target], cwd=self.top)

    def reset(
        self,
        target: str | None = None,
        *,
        yes: bool = False,
        keep_ignored: bool = False,
    ) -> None:
        if not yes:
            raise RuntimeError("Pass --yes to reset and clean the working tree.")
        self.fetch_all()
        ref = target or "@{u}"
        result = run_git(["rev-parse", ref], cwd=self.top, check=False)
        if result.returncode != 0:
            ref = self.canonical_main_ref()
        run_git(["reset", "--hard", ref], cwd=self.top)
        clean_args = ["clean", "-fd"] if keep_ignored else ["clean", "-fdx"]
        run_git(clean_args, cwd=self.top)

    def revert(
        self,
        sha: str,
        *,
        merge_parent: int | None = None,
        continue_: bool = False,
        abort: bool = False,
    ) -> None:
        if abort:
            run_git(["revert", "--abort"], cwd=self.top)
            return
        if continue_:
            run_git(["revert", "--continue"], cwd=self.top)
            return
        args = ["revert", "--no-edit"]
        if merge_parent is not None:
            args.extend(["-m", str(merge_parent)])
        args.append(sha)
        run_git(args, cwd=self.top)

    def cherry_pick(
        self,
        sha: str,
        *,
        continue_: bool = False,
        abort: bool = False,
    ) -> None:
        if abort:
            run_git(["cherry-pick", "--abort"], cwd=self.top)
            return
        if continue_:
            run_git(["cherry-pick", "--continue"], cwd=self.top)
            return
        run_git(["cherry-pick", "--no-edit", sha], cwd=self.top)

    def tag(
        self,
        name: str | None = None,
        *,
        push: bool = False,
        replace_local: bool = False,
        force_push: bool = False,
        yes: bool = False,
    ) -> str:
        from datetime import date

        tag_name = name or date.today().isoformat()
        if push and not yes:
            raise RuntimeError("Pass --yes to push tag to remote.")
        if force_push and not yes:
            raise RuntimeError("Pass --yes to force-push tag.")
        if replace_local and not yes:
            raise RuntimeError("Pass --yes to replace local tag.")
        if yes:
            self.align_main(yes=True)
        target = "HEAD"
        exists = run_git(
            ["rev-parse", "-q", "--verify", f"refs/tags/{tag_name}"],
            cwd=self.top,
            check=False,
        ).returncode == 0
        if exists and replace_local:
            run_git(["tag", "-fa", tag_name, target, "-m", tag_name], cwd=self.top)
        elif not exists:
            run_git(["tag", "-a", tag_name, target, "-m", tag_name], cwd=self.top)
        if push and self.remote_exists("origin"):
            if force_push:
                run_git(["push", "--force", "origin", f"refs/tags/{tag_name}"], cwd=self.top)
            else:
                run_git(["push", "origin", f"refs/tags/{tag_name}"], cwd=self.top)
        return tag_name

    def large_files(self, top_n: int = 20, *, worktree: bool = False) -> list[tuple[int, str]]:
        root = Path(self.top)
        files: list[tuple[int, Path]] = []
        if worktree:
            for path in root.rglob("*"):
                if path.is_file() and ".git" not in path.parts:
                    try:
                        files.append((path.stat().st_size, path))
                    except OSError:
                        pass
        else:
            out = run_git(["ls-files", "-z"], cwd=self.top).stdout
            for part in out.split("\0"):
                if not part:
                    continue
                p = root / part
                if p.is_file():
                    try:
                        files.append((p.stat().st_size, p))
                    except OSError:
                        pass
        files.sort(reverse=True)
        return [(size, str(path.relative_to(root))) for size, path in files[:top_n]]
