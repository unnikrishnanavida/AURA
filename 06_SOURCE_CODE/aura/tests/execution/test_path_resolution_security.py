"""Supplementary workspace path-resolution security tests (Phase 39, WORKSTREAM H).

These validate the pathological-path rejection implemented in
:class:`~aura.execution.actions.Workspace` on hosts where OS symlink creation
is not permitted. They are SUPPLEMENTARY evidence to the symlink-escape test,
which remains skipped here (Windows requires symlink privilege) and must still
be run on a capable host.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aura.execution.actions import Workspace, WorkspaceError, _within


@pytest.fixture
def workspace(tmp_path: Path) -> Workspace:
    ws = Workspace(tmp_path / "ws", create=True)
    (ws.root / "a").mkdir()
    (ws.root / "a" / "b.txt").write_text("ok", encoding="utf-8")
    return ws


def test_relative_path_within_resolves(workspace: Workspace) -> None:
    assert workspace.resolve("a/b.txt") == (workspace.root / "a" / "b.txt")
    assert workspace.resolve(".") == workspace.root


def test_parent_traversal_rejected(workspace: Workspace) -> None:
    with pytest.raises(WorkspaceError):
        workspace.resolve("../../escape.txt")
    with pytest.raises(WorkspaceError):
        workspace.resolve("a/../../escape.txt")  # normalization still escapes


def test_deep_traversal_rejected(workspace: Workspace) -> None:
    with pytest.raises(WorkspaceError):
        workspace.resolve("a/../../../etc/passwd")


def test_absolute_inside_root_accepted(workspace: Workspace) -> None:
    target = str((workspace.root / "a" / "b.txt").resolve())
    assert workspace.resolve(target) == workspace.root / "a" / "b.txt"


def test_absolute_outside_root_rejected(workspace: Workspace, tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    with pytest.raises(WorkspaceError):
        workspace.resolve(str(outside))


def test_null_and_empty_paths_rejected(workspace: Workspace) -> None:
    with pytest.raises(WorkspaceError):
        workspace.resolve(None)  # type: ignore[arg-type]
    # Empty relative resolves to the root and is allowed by design:
    assert workspace.resolve("") == workspace.root


def test_normalized_containment_check() -> None:
    root = Path("C:/work/ws")
    assert _within(root, root / "a" / "b")
    assert _within(root, Path("c:/work/ws/x"))
    assert not _within(root, Path("C:/work/wsx"))  # prefix is not containment
    assert not _within(root, Path("C:/work"))