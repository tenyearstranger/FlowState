from __future__ import annotations

from pathlib import Path

import pytest

from src.services.git_service import GitError, GitService

if not GitService().is_git_available():
    pytest.skip("git command is not available", allow_module_level=True)


def _init_repo_with_baseline(tmp_path: Path) -> tuple[GitService, Path, str]:
    service = GitService()
    repo = tmp_path / "repo"
    repo.mkdir()
    service.init_repo(repo)
    base_sha = service.baseline_commit(repo)
    return service, repo, base_sha


def test_init_repo_and_baseline_commit_for_empty_directory(tmp_path: Path):
    service = GitService()
    repo = tmp_path / "empty-repo"
    repo.mkdir()

    service.init_repo(repo)
    baseline_sha = service.baseline_commit(repo)

    assert baseline_sha
    assert service.head_commit(repo) == baseline_sha
    assert service.current_branch(repo) == "main"


def test_init_repo_and_baseline_commit_for_non_empty_directory(tmp_path: Path):
    service = GitService()
    repo = tmp_path / "non-empty-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")

    service.init_repo(repo)
    baseline_sha = service.baseline_commit(repo)

    assert baseline_sha
    assert service.head_commit(repo) == baseline_sha
    assert (repo / "README.md").exists()


def test_find_enclosing_repo_for_nested_path(tmp_path: Path):
    service, repo, _ = _init_repo_with_baseline(tmp_path)
    nested = repo / "apps" / "api"
    nested.mkdir(parents=True)

    assert service.find_enclosing_repo(nested) == repo
    assert service.find_repo_root(nested) == repo


def test_ensure_flowstate_worktree_ignore_replaces_broad_rule(tmp_path: Path):
    service = GitService()
    repo = tmp_path / "repo-ignore"
    repo.mkdir()
    gitignore = repo / ".gitignore"
    gitignore.write_text(".flowstate/\nnode_modules/\n", encoding="utf-8")

    service.ensure_flowstate_worktree_ignore(repo)

    content = gitignore.read_text(encoding="utf-8")
    assert ".flowstate/\n" not in content
    assert ".flowstate/worktrees/" in content
    assert "node_modules/" in content


def test_add_and_remove_worktree_and_delete_branch(tmp_path: Path):
    service, repo, base_sha = _init_repo_with_baseline(tmp_path)
    worktree = repo / ".flowstate" / "worktrees" / "pipe-test"
    branch = "devflow/pipe-test"

    service.add_worktree(repo, worktree, branch, base=base_sha)
    assert worktree.exists()
    assert service.current_branch(worktree) == branch

    service.remove_worktree(repo, worktree, force=True)
    assert not worktree.exists()

    service.delete_branch(repo, branch, force=True)
    with pytest.raises(GitError):
        service.delete_branch(repo, branch, force=True)


def test_commit_with_and_without_changes(tmp_path: Path):
    service, repo, _ = _init_repo_with_baseline(tmp_path)
    (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")

    assert service.has_changes(repo) is True
    service.stage_all(repo)
    commit_sha = service.commit(repo, "feat: add app")
    assert commit_sha == service.head_commit(repo)
    assert service.has_changes(repo) is False

    with pytest.raises(GitError):
        service.commit(repo, "chore: no-op commit")


def test_diff_diff_stats_changed_files_and_reset(tmp_path: Path):
    service, repo, base_sha = _init_repo_with_baseline(tmp_path)
    target = repo / "note.txt"
    target.write_text("line-1\n", encoding="utf-8")
    service.stage_all(repo)
    first_sha = service.commit(repo, "feat: add note")

    target.write_text("line-1\nline-2\n", encoding="utf-8")
    service.stage_all(repo)
    second_sha = service.commit(repo, "feat: update note")

    diff_text = service.diff(repo, base=first_sha, head=second_sha)
    stats = service.diff_stats(repo, base=first_sha, head=second_sha)
    changed_files = service.changed_files(repo, base=base_sha, head=second_sha)

    assert "+line-2" in diff_text
    assert stats["files"] >= 1
    assert stats["insertions"] >= 1
    assert "note.txt" in changed_files

    service.reset_hard(repo, first_sha)
    assert service.head_commit(repo) == first_sha
    assert target.read_text(encoding="utf-8") == "line-1\n"
