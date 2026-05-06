"""Tests for envault.search."""

import pytest

from envault.search import SearchResult, SearchSummary, search

SAMPLE_ENV = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "REDIS_URL": "redis://localhost:6379",
    "SECRET_KEY": "supersecret",
    "DEBUG": "true",
    "API_KEY": "abc123",
    "app_mode": "production",
}


def test_search_by_key_returns_matching_keys():
    result = search(SAMPLE_ENV, "URL")
    keys = {r.key for r in result.results}
    assert keys == {"DATABASE_URL", "REDIS_URL"}


def test_search_by_key_is_case_insensitive_by_default():
    result = search(SAMPLE_ENV, "url")
    assert result.count == 2


def test_search_by_key_case_sensitive():
    result = search(SAMPLE_ENV, "url", case_sensitive=True)
    assert result.is_empty


def test_search_by_value_not_enabled_by_default():
    result = search(SAMPLE_ENV, "postgres")
    assert result.is_empty


def test_search_by_value_when_enabled():
    result = search(SAMPLE_ENV, "localhost", search_values=True)
    keys = {r.key for r in result.results}
    assert keys == {"DATABASE_URL", "REDIS_URL"}


def test_search_matched_by_key():
    result = search(SAMPLE_ENV, "DEBUG")
    assert result.count == 1
    assert result.results[0].matched_by == "key"


def test_search_matched_by_value():
    result = search(SAMPLE_ENV, "supersecret", search_keys=False, search_values=True)
    assert result.count == 1
    assert result.results[0].matched_by == "value"


def test_search_matched_by_both():
    # KEY contains 'key', value of API_KEY contains 'key' too? No — use a crafted env.
    env = {"KEY_NAME": "my_key_value"}
    result = search(env, "key", search_keys=True, search_values=True)
    assert result.count == 1
    assert result.results[0].matched_by == "both"


def test_search_regex_pattern():
    result = search(SAMPLE_ENV, r"^API", use_regex=True)
    assert result.count == 1
    assert result.results[0].key == "API_KEY"


def test_search_invalid_regex_returns_no_results():
    result = search(SAMPLE_ENV, r"[invalid", use_regex=True)
    assert result.is_empty


def test_search_empty_env_returns_empty_summary():
    result = search({}, "anything")
    assert result.is_empty
    assert result.count == 0


def test_search_no_match_returns_empty_summary():
    result = search(SAMPLE_ENV, "NONEXISTENT")
    assert result.is_empty


def test_search_summary_stores_query():
    result = search(SAMPLE_ENV, "DEBUG")
    assert result.query == "DEBUG"


def test_search_results_are_sorted_alphabetically():
    result = search(SAMPLE_ENV, "url")
    keys = [r.key for r in result.results]
    assert keys == sorted(keys)
