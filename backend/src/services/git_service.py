from __future__ import annotations

"""Git 命令封装。"""

from pathlib import Path
import shutil
import subprocess


class GitError(RuntimeError):
    """Git 命令执行失败。"""


class NotARepoError(GitError):
    """目标目录不是 Git 仓库。"""


class NestedRepoError(GitError):
    """目标目录位于上层 Git 仓库内。"""


class WorktreeBusyError(GitError):
    """worktree 无法创建或清理。"""


class GitService:
    """纯命令封装，无业务语义。"""

    def __init__(self, *, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds

    def is_git_available(self) -> bool:
        try:
            self._run(["--version"], cwd=None)
            return True
        except GitError:
            return False

    # ---- 仓库探测 ----
    def is_git_repo(self, path: Path) -> bool:
        try:
            self._run(["rev-parse", "--is-inside-work-tree"], cwd=path)
            return True
        except GitError:
            return False

    def find_repo_root(self, path: Path) -> Path | None:
        try:
            output = self._run(["rev-parse", "--show-toplevel"], cwd=path)
        except GitError:
            return None
        return Path(output.strip()).resolve()

    def find_enclosing_repo(self, path: Path) -> Path | None:
        current = path.resolve()
        for candidate in (current, *current.parents):
            if (candidate / ".git").exists():
                return candidate
        return None

    # ---- 仓库初始化 ----
    def init_repo(self, path: Path, *, default_branch: str = "main") -> None:
        try:
            self._run(["init", "-b", default_branch], cwd=path)
            return
        except GitError:
            self._run(["init"], cwd=path)
        try:
            self._run(["symbolic-ref", "HEAD", f"refs/heads/{default_branch}"], cwd=path)
        except GitError:
            self._run(["checkout", "-B", default_branch], cwd=path)

    def write_default_gitignore(self, path: Path) -> None:
        self.ensure_flowstate_worktree_ignore(path)
        self.ensure_gitignore_entry(path, ".devflow_state/")

    def baseline_commit(self, path: Path, message: str = "chore: flowstate baseline") -> str:
        self.stage_all(path)
        return self.commit(path, message, allow_empty=True)

    # ---- 分支与 worktree ----
    def current_branch(self, repo: Path) -> str:
        output = self._run(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo)
        branch = output.strip()
        if not branch:
            raise NotARepoError(f"无法解析当前分支: {repo}")
        return branch

    def head_commit(self, repo: Path) -> str:
        output = self._run(["rev-parse", "HEAD"], cwd=repo)
        sha = output.strip()
        if not sha:
            raise NotARepoError(f"无法解析 HEAD: {repo}")
        return sha

    def add_worktree(
        self,
        repo: Path,
        worktree_path: Path,
        branch: str,
        *,
        base: str,
    ) -> None:
        if worktree_path.exists():
            try:
                shutil.rmtree(worktree_path)
            except OSError as exc:
                raise WorktreeBusyError(f"清理残留 worktree 失败: {worktree_path}") from exc

        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._run(
                ["worktree", "add", str(worktree_path), "-b", branch, base],
                cwd=repo,
                timeout_seconds=max(self.timeout_seconds, 60),
            )
        except GitError as exc:
            raise WorktreeBusyError(str(exc)) from exc

    def remove_worktree(self, repo: Path, worktree_path: Path, *, force: bool = False) -> None:
        args = ["worktree", "remove", str(worktree_path)]
        if force:
            args.append("--force")
        self._run(args, cwd=repo, timeout_seconds=max(self.timeout_seconds, 60))

    def delete_branch(self, repo: Path, branch: str, *, force: bool = True) -> None:
        args = ["branch", "-D" if force else "-d", branch]
        self._run(args, cwd=repo)

    # ---- 提交 ----
    def stage_all(self, worktree: Path) -> None:
        self._run(["add", "-A"], cwd=worktree)

    def commit(self, worktree: Path, message: str, *, allow_empty: bool = False) -> str:
        if not allow_empty and not self.has_changes(worktree):
            raise GitError("NO_CHANGES")

        args = [
            "-c",
            "user.name=FlowState Bot",
            "-c",
            "user.email=flowstate@local",
            "commit",
            "-m",
            message,
        ]
        if allow_empty:
            args.append("--allow-empty")
        self._run(args, cwd=worktree)
        return self.head_commit(worktree)

    def has_changes(self, worktree: Path) -> bool:
        output = self._run(["status", "--porcelain"], cwd=worktree)
        return bool(output.strip())

    # ---- 查询 ----
    def diff(self, worktree: Path, *, base: str, head: str = "HEAD") -> str:
        return self._run(["diff", "--no-ext-diff", f"{base}..{head}"], cwd=worktree)

    def diff_stats(self, worktree: Path, *, base: str, head: str = "HEAD") -> dict:
        output = self._run(["diff", "--numstat", f"{base}..{head}"], cwd=worktree)
        files = 0
        insertions = 0
        deletions = 0
        for line in output.splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            files += 1
            add_text, del_text = parts[0], parts[1]
            if add_text.isdigit():
                insertions += int(add_text)
            if del_text.isdigit():
                deletions += int(del_text)
        return {"files": files, "insertions": insertions, "deletions": deletions}

    def changed_files(self, worktree: Path, *, base: str, head: str = "HEAD") -> list[str]:
        output = self._run(["diff", "--name-only", f"{base}..{head}"], cwd=worktree)
        return [line.strip() for line in output.splitlines() if line.strip()]

    def show_commit(self, worktree: Path, sha: str) -> dict:
        body = self._run(["show", "--quiet", "--format=%H%n%s%n%B", sha], cwd=worktree)
        lines = body.splitlines()
        return {
            "sha": lines[0].strip() if lines else sha,
            "subject": lines[1].strip() if len(lines) > 1 else "",
            "message": "\n".join(lines[2:]).strip() if len(lines) > 2 else "",
        }

    # ---- 回退 ----
    def reset_hard(self, worktree: Path, ref: str) -> None:
        self._run(["reset", "--hard", ref], cwd=worktree, timeout_seconds=max(self.timeout_seconds, 60))

    def clean_untracked(self, worktree: Path) -> None:
        self._run(["clean", "-fd"], cwd=worktree, timeout_seconds=max(self.timeout_seconds, 60))

    def has_remote(self, repo: Path, remote: str = "origin") -> bool:
        """Check whether a named remote exists."""
        try:
            output = self._run(["remote"], cwd=repo)
            return remote in output.splitlines()
        except GitError:
            return False

    def push_branch(self, repo: Path, branch: str, remote: str = "origin") -> None:
        """Push branch to remote. Raises GitError on failure."""
        self._run(
            ["push", "--set-upstream", remote, branch],
            cwd=repo,
            timeout_seconds=60,
        )

    def create_gh_pr(
        self,
        repo: Path,
        *,
        title: str,
        body: str,
        head: str,
        base: str,
    ) -> str:
        """Run `gh pr create` and return the PR URL. Raises GitError if gh unavailable or fails."""
        import subprocess as _sp
        import shutil

        if not shutil.which("gh"):
            raise GitError("gh CLI 未安装，无法自动创建 PR")

        cmd = [
            "gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--head", head,
            "--base", base,
        ]
        try:
            result = _sp.run(
                cmd,
                cwd=str(repo),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=60,
            )
        except _sp.TimeoutExpired as exc:
            raise GitError("gh pr create 超时") from exc

        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            raise GitError(f"gh pr create 失败: {stderr or result.stdout}")

        # gh outputs the PR URL as the last line
        url = (result.stdout or "").strip().splitlines()[-1].strip()
        if not url.startswith("http"):
            raise GitError(f"gh pr create 输出异常: {result.stdout[:200]}")
        return url

    def ensure_gitignore_entry(self, repo: Path, entry: str) -> None:
        gitignore_path = repo / ".gitignore"
        normalized = entry.strip()
        if not normalized:
            return
        existing = gitignore_path.read_text(encoding="utf-8").splitlines() if gitignore_path.exists() else []
        if normalized in existing:
            return
        existing.append(normalized)
        gitignore_path.write_text("\n".join(existing).rstrip() + "\n", encoding="utf-8")

    def ensure_flowstate_worktree_ignore(self, repo: Path) -> None:
        gitignore_path = repo / ".gitignore"
        existing = gitignore_path.read_text(encoding="utf-8").splitlines() if gitignore_path.exists() else []
        normalized_lines: list[str] = []
        replaced = False
        for line in existing:
            if line.strip() == ".flowstate/":
                if not replaced:
                    normalized_lines.append(".flowstate/worktrees/")
                    replaced = True
                continue
            normalized_lines.append(line)

        if ".flowstate/worktrees/" not in normalized_lines:
            normalized_lines.append(".flowstate/worktrees/")
        gitignore_path.write_text("\n".join(normalized_lines).rstrip() + "\n", encoding="utf-8")

    def _run(
        self,
        args: list[str],
        *,
        cwd: Path | None,
        timeout_seconds: int | None = None,
    ) -> str:
        cmd = ["git", *args]
        try:
            completed = subprocess.run(
                cmd,
                cwd=str(cwd) if cwd is not None else None,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                timeout=timeout_seconds or self.timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise GitError("未安装 git 命令") from exc
        except subprocess.TimeoutExpired as exc:
            raise GitError(f"git 命令超时: {' '.join(cmd)}") from exc

        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()
            message = stderr or stdout or f"git 命令失败: {' '.join(cmd)}"
            raise GitError(message)

        return completed.stdout or ""
