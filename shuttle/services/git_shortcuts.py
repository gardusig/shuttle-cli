from __future__ import annotations

import os
import time
from pathlib import Path

from shuttle.utils.process import GitCommandError, run_git
from shuttle.utils.quick_defaults import default_tag_name


class GitShortcuts:
    """Local git operations with safety gates for destructive actions."""

    def __init__(self, top: str | None = None) -> None:
        self.top = top or os.environ.get("SHUTTLE_GIT_ROOT") or self.repo_root()

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

    def local_branch_names(self, *, exclude_main: bool = True) -> list[str]:
        out = run_git(
            ["for-each-ref", "--format=%(refname:short)", "refs/heads/"],
            cwd=self.top,
        ).stdout
        names = [line.strip() for line in out.splitlines() if line.strip()]
        if exclude_main:
            names = [name for name in names if name != "main"]
        return sorted(names)

    def remote_branch_names(self, remote: str = "origin") -> list[str]:
        if not self.remote_exists(remote):
            return []
        out = run_git(
            ["for-each-ref", "--format=%(refname:short)", f"refs/remotes/{remote}/"],
            cwd=self.top,
            check=False,
        ).stdout
        prefix = f"{remote}/"
        names: list[str] = []
        for line in out.splitlines():
            ref = line.strip()
            if not ref or ref.endswith("/HEAD") or ref == f"{remote}/HEAD":
                continue
            short = ref[len(prefix) :] if ref.startswith(prefix) else ref
            if short in {"main", "HEAD"}:
                continue
            names.append(short)
        return sorted(set(names))

    def clear_branches_local(
        self,
        *,
        yes: bool = False,
        keep_ignored: bool = False,
    ) -> list[str]:
        """Align main (reset + clean), then delete every local branch except main."""
        if not yes:
            raise RuntimeError("Pass --yes to clear all local branches.")
        self.align_main(yes=True, keep_ignored=keep_ignored)
        deleted: list[str] = []
        for name in self.local_branch_names(exclude_main=True):
            run_git(["branch", "-D", name], cwd=self.top)
            deleted.append(name)
        return deleted

    def delete_remote_branches(self, *, yes: bool = False, remote: str = "origin") -> list[str]:
        if not yes:
            raise RuntimeError("Pass --yes to delete remote branches.")
        if not self.remote_exists(remote):
            return []
        self.fetch_all(prune=True)
        deleted: list[str] = []
        for name in self.remote_branch_names(remote):
            result = run_git(
                ["push", remote, "--delete", name],
                cwd=self.top,
                check=False,
            )
            if result.returncode == 0:
                deleted.append(name)
        return deleted

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

    def tag_exists_local(self, name: str) -> bool:
        result = run_git(
            ["rev-parse", "-q", "--verify", f"refs/tags/{name}"],
            cwd=self.top,
            check=False,
        )
        return result.returncode == 0

    def tag_exists_remote(self, name: str, remote: str = "origin") -> bool:
        if not self.remote_exists(remote):
            return False
        result = run_git(
            ["ls-remote", "--tags", remote, f"refs/tags/{name}"],
            cwd=self.top,
            check=False,
        )
        return bool(result.stdout.strip())

    def create_tag(self, name: str, *, replace: bool = False) -> None:
        if self.tag_exists_local(name):
            if not replace:
                raise RuntimeError(
                    f"Tag {name} already exists locally. Pass replace=True to overwrite."
                )
            run_git(["tag", "-fa", name, "HEAD", "-m", name], cwd=self.top)
        else:
            run_git(["tag", "-a", name, "HEAD", "-m", name], cwd=self.top)

    def push_tag(self, name: str, *, force: bool = False, remote: str = "origin") -> None:
        if not self.remote_exists(remote):
            raise RuntimeError(f"Remote {remote} is not configured.")
        if force:
            run_git(["push", "--force", remote, f"refs/tags/{name}"], cwd=self.top)
        else:
            run_git(["push", remote, f"refs/tags/{name}"], cwd=self.top)

    def zip_tag(self, tag: str, output: Path) -> Path:
        run_git(["rev-parse", "-q", "--verify", f"refs/tags/{tag}"], cwd=self.top)
        output.parent.mkdir(parents=True, exist_ok=True)
        run_git(
            ["archive", "--format=zip", f"--output={output}", tag],
            cwd=self.top,
        )
        return output

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
