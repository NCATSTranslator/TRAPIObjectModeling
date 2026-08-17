"""Tests for translator_tom.utils.cache."""

from __future__ import annotations

import copy

from translator_tom.utils.cache import lru_copy_cache


def test_returns_copy_not_shared_instance():
    @lru_copy_cache()
    def make() -> list[int]:
        return [1, 2, 3]

    a = make()
    a.append(99)  # mutating a caller's result must not poison the cache
    b = make()
    assert b == [1, 2, 3]
    assert a is not b


def test_computes_once_per_key():
    calls = {"n": 0}

    @lru_copy_cache()
    def f(x: int) -> list[int]:
        calls["n"] += 1
        return [x]

    f(1)
    f(1)
    f(2)
    assert calls["n"] == 2  # only distinct args recompute


def test_distinct_args_distinct_results():
    @lru_copy_cache()
    def f(x: int) -> set[int]:
        return {x}

    assert f(1) == {1}
    assert f(2) == {2}


def test_cache_clear_and_info():
    calls = {"n": 0}

    @lru_copy_cache()
    def f() -> list[int]:
        calls["n"] += 1
        return [0]

    f()
    f()
    assert calls["n"] == 1
    assert f.cache_info().hits >= 1
    f.cache_clear()
    f()
    assert calls["n"] == 2


def test_shallow_copy_shares_elements():
    sentinel = object()

    @lru_copy_cache()
    def f() -> list[object]:
        return [sentinel]

    assert f() is not f()  # fresh container each call
    assert f()[0] is sentinel  # shallow: elements shared


def test_deepcopy_copier_isolates_nested():
    @lru_copy_cache(copier=copy.deepcopy)
    def f() -> list[list[int]]:
        return [[1, 2]]

    a = f()
    a[0].append(3)  # nested mutation must not leak back into the cache
    assert f() == [[1, 2]]
