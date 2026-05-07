"""Tests for envault.merge."""
import pytest

from envault.merge import (
    MergeStrategy,
    MergeResult,
    merge,
)


LOCAL = {"A": "1", "B": "2", "C": "3"}
REMOTE = {"A": "1", "B": "99", "D": "4"}


def test_merge_ours_keeps_local_on_conflict():
    result = merge(LOCAL, REMOTE, strategy=MergeStrategy.OURS)
    assert result.merged["B"] == "2"


def test_merge_theirs_keeps_remote_on_conflict():
    result = merge(LOCAL, REMOTE, strategy=MergeStrategy.THEIRS)
    assert result.merged["B"] == "99"


def test_merge_adds_remote_only_keys():
    result = merge(LOCAL, REMOTE)
    assert result.merged["D"] == "4"


def test_merge_keeps_local_only_keys():
    result = merge(LOCAL, REMOTE)
    assert result.merged["C"] == "3"


def test_merge_records_conflicts():
    result = merge(LOCAL, REMOTE)
    assert result.has_conflicts
    keys = [c[0] for c in result.conflicts]
    assert "B" in keys


def test_merge_conflict_tuple_contains_both_values():
    result = merge(LOCAL, REMOTE)
    conflict = next(c for c in result.conflicts if c[0] == "B")
    assert conflict[1] == "2"   # local
    assert conflict[2] == "99"  # remote


def test_merge_no_conflicts_when_identical():
    env = {"X": "1", "Y": "2"}
    result = merge(env, env.copy())
    assert not result.has_conflicts


def test_merge_added_lists_remote_only_keys():
    result = merge(LOCAL, REMOTE)
    assert "D" in result.added
    assert "A" not in result.added


def test_merge_removed_lists_local_only_keys():
    result = merge(LOCAL, REMOTE)
    assert "C" in result.removed
    assert "D" not in result.removed


def test_merge_empty_local():
    result = merge({}, {"X": "1"})
    assert result.merged == {"X": "1"}
    assert not result.has_conflicts


def test_merge_empty_remote():
    result = merge({"X": "1"}, {})
    assert result.merged == {"X": "1"}
    assert not result.has_conflicts


def test_merge_both_empty():
    result = merge({}, {})
    assert result.merged == {}
    assert not result.has_conflicts


def test_merge_result_summary_contains_conflict_info():
    result = merge(LOCAL, REMOTE)
    summary = result.summary()
    assert "Conflicts" in summary
    assert "B" in summary


def test_merge_result_summary_no_changes():
    env = {"K": "v"}
    result = merge(env, env.copy())
    # no added, no removed (same keys), no conflicts
    result.added = []
    result.removed = []
    assert "No changes" in result.summary()


def test_merge_union_strategy_same_as_ours_on_conflict():
    result_ours = merge(LOCAL, REMOTE, strategy=MergeStrategy.OURS)
    result_union = merge(LOCAL, REMOTE, strategy=MergeStrategy.UNION)
    assert result_ours.merged == result_union.merged
