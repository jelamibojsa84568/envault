"""Tests for envault.access module."""

import pytest
from pathlib import Path

from envault.access import (
    grant,
    revoke,
    get_role,
    require_role,
    list_users,
    AccessDeniedError,
    InvalidRoleError,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_grant_and_get_role(vault_dir):
    grant(vault_dir, "alice", "write")
    assert get_role(vault_dir, "alice") == "write"


def test_grant_overwrites_existing_role(vault_dir):
    grant(vault_dir, "alice", "read")
    grant(vault_dir, "alice", "admin")
    assert get_role(vault_dir, "alice") == "admin"


def test_grant_invalid_role_raises(vault_dir):
    with pytest.raises(InvalidRoleError):
        grant(vault_dir, "alice", "superuser")


def test_revoke_existing_user_returns_true(vault_dir):
    grant(vault_dir, "bob", "read")
    assert revoke(vault_dir, "bob") is True
    assert get_role(vault_dir, "bob") is None


def test_revoke_nonexistent_user_returns_false(vault_dir):
    assert revoke(vault_dir, "nobody") is False


def test_get_role_returns_none_for_unknown_user(vault_dir):
    assert get_role(vault_dir, "ghost") is None


def test_require_role_passes_for_exact_role(vault_dir):
    grant(vault_dir, "carol", "write")
    require_role(vault_dir, "carol", "write")  # should not raise


def test_require_role_passes_for_higher_role(vault_dir):
    grant(vault_dir, "carol", "admin")
    require_role(vault_dir, "carol", "read")  # admin satisfies read


def test_require_role_raises_for_insufficient_role(vault_dir):
    grant(vault_dir, "dave", "read")
    with pytest.raises(AccessDeniedError):
        require_role(vault_dir, "dave", "write")


def test_require_role_raises_for_unknown_user(vault_dir):
    with pytest.raises(AccessDeniedError):
        require_role(vault_dir, "unknown", "read")


def test_list_users_returns_all_entries(vault_dir):
    grant(vault_dir, "alice", "admin")
    grant(vault_dir, "bob", "read")
    users = list_users(vault_dir)
    assert users == {"alice": "admin", "bob": "read"}


def test_list_users_empty_when_no_grants(vault_dir):
    assert list_users(vault_dir) == {}


def test_access_file_is_valid_json(vault_dir):
    import json
    grant(vault_dir, "alice", "write")
    access_file = vault_dir / ".envault_access.json"
    data = json.loads(access_file.read_text())
    assert data["alice"] == "write"
