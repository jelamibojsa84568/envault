"""Tests for envault/profiles.py."""

import pytest
from pathlib import Path

from envault.profiles import (
    set_profile,
    remove_profile,
    get_profile,
    list_profiles,
    active_profile,
    set_active_profile,
    ProfileNotFoundError,
    ProfilesCorruptedError,
    _profiles_path,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_set_profile_creates_file(vault_dir):
    set_profile(vault_dir, "dev", "vault_dev.json")
    assert _profiles_path(vault_dir).exists()


def test_set_profile_stores_mapping(vault_dir):
    set_profile(vault_dir, "staging", "vault_staging.json")
    assert get_profile(vault_dir, "staging") == "vault_staging.json"


def test_set_profile_overwrites_existing(vault_dir):
    set_profile(vault_dir, "prod", "vault_prod_v1.json")
    set_profile(vault_dir, "prod", "vault_prod_v2.json")
    assert get_profile(vault_dir, "prod") == "vault_prod_v2.json"


def test_list_profiles_returns_sorted(vault_dir):
    set_profile(vault_dir, "prod", "p.json")
    set_profile(vault_dir, "dev", "d.json")
    set_profile(vault_dir, "staging", "s.json")
    assert list_profiles(vault_dir) == ["dev", "prod", "staging"]


def test_list_profiles_empty(vault_dir):
    assert list_profiles(vault_dir) == []


def test_get_profile_missing_raises(vault_dir):
    with pytest.raises(ProfileNotFoundError):
        get_profile(vault_dir, "nonexistent")


def test_remove_profile_returns_true(vault_dir):
    set_profile(vault_dir, "dev", "d.json")
    assert remove_profile(vault_dir, "dev") is True


def test_remove_profile_actually_removes(vault_dir):
    set_profile(vault_dir, "dev", "d.json")
    remove_profile(vault_dir, "dev")
    assert "dev" not in list_profiles(vault_dir)


def test_remove_profile_missing_returns_false(vault_dir):
    assert remove_profile(vault_dir, "ghost") is False


def test_active_profile_none_when_no_sentinel(vault_dir):
    assert active_profile(vault_dir) is None


def test_set_active_profile_persists(vault_dir):
    set_profile(vault_dir, "dev", "d.json")
    set_active_profile(vault_dir, "dev")
    assert active_profile(vault_dir) == "dev"


def test_set_active_profile_unknown_raises(vault_dir):
    with pytest.raises(ProfileNotFoundError):
        set_active_profile(vault_dir, "ghost")


def test_profiles_corrupted_raises(vault_dir):
    _profiles_path(vault_dir).write_text("not json{{{")
    with pytest.raises(ProfilesCorruptedError):
        list_profiles(vault_dir)
