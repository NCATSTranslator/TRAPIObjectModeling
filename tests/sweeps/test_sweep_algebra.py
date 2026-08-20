"""Reflection-driven algebraic-property sweep over the merge/normalize utilities.

Each merge/normalize method should satisfy a small algebraic law; this sweeps those
laws over every model / `DictUtil` that exposes the relevant method, using the bare
instances from `_sweep_helpers`, so new models are covered automatically:

1. update-with-empty is identity: `x.update(<empty>)` must not change `x.hash()`.
2. normalize idempotence: a second `normalize` is a no-op on already-normalized data.
3. single-element merge identity: `merge_results([x])` yields `[x]` unchanged.

Method signatures vary (some `update`/`normalize` take extra kwargs or a required
`mapping`, some return a tuple), so each sweep inspects the signature and drives the
call accordingly. Candidates that expose the method but can't be driven safely (e.g.
no no-arg `new()` and required fields, so no empty `other` is constructible) are
skipped with a documented reason rather than dropped silently.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

import pytest
from _sweep_helpers import sweep_id, DICTUTILS, MODELS, build

from translator_tom import TOMBase
from translator_tom.utils.dict_util_base import DictUtil

_POSITIONAL = (
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
)


def _no_required_params(fn: Callable[..., Any]) -> bool:
    """Whether `fn` can be called with no arguments (all params optional/variadic)."""
    try:
        params = inspect.signature(fn).parameters.values()
    except (TypeError, ValueError):
        return False
    return all(
        p.default is not inspect.Parameter.empty
        or p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        for p in params
    )


def _model_has_no_required_fields(model: type[TOMBase]) -> bool:
    """Whether an empty instance is constructible via `model_construct()` (no required fields)."""
    return not any(field.is_required() for field in model.model_fields.values())


# --- Property 1: update-with-empty is identity ----------------------------------------

_UPDATE_MODELS = [m for m in MODELS if hasattr(m, "update")]
_UPDATE_DICTUTILS = [(m, du) for m, du in DICTUTILS if hasattr(du, "update")]


def _empty_model(model: type[TOMBase]) -> tuple[TOMBase | None, str | None]:
    """An empty same-type instance to merge in, or `(None, reason)` if none is constructible."""
    new = getattr(model, "new", None)
    if callable(new) and _no_required_params(new):
        return new(), None
    if _model_has_no_required_fields(model):
        return model.model_construct(), None
    return (
        None,
        "no no-arg new() and has required fields; empty `other` not constructible",
    )


def _empty_dict(
    model: type[TOMBase], du: type[DictUtil[Any]]
) -> tuple[dict[str, Any] | None, str | None]:
    """An empty dict to merge in, or `(None, reason)` if none is constructible."""
    new = getattr(du, "new", None)
    if callable(new) and _no_required_params(new):
        return new(), None
    if _model_has_no_required_fields(model):
        return {}, None
    return (
        None,
        "no no-arg new() and model has required fields; empty `other` not constructible",
    )


@pytest.mark.parametrize(
    "model", _UPDATE_MODELS, ids=[sweep_id(m) for m in _UPDATE_MODELS]
)
def test_update_with_empty_is_identity(model: type[TOMBase]) -> None:
    empty, reason = _empty_model(model)
    if reason is not None:
        pytest.skip(reason)
    x = build(model)
    # First merge settles any build-arbitrary container keys (e.g. KnowledgeGraph
    # re-keys edges to their hash on update). Merging empty into a *settled* instance
    # must then be a true no-op. (Ignore any (old:new) mapping tuple update returns.)
    x.update(empty)
    before = x.hash()
    x.update(empty)
    assert x.hash() == before


@pytest.mark.parametrize(
    ("model", "dictutil"),
    _UPDATE_DICTUTILS,
    ids=[sweep_id(du) for _, du in _UPDATE_DICTUTILS],
)
def test_update_with_empty_is_identity_dictutil(
    model: type[TOMBase], dictutil: type[DictUtil[Any]]
) -> None:
    empty, reason = _empty_dict(model, dictutil)
    if reason is not None:
        pytest.skip(reason)
    x = build(model).to_dict()
    dictutil.update(x, empty)  # settle build-arbitrary keys, mirroring the model test
    before = dictutil.hash(x)
    dictutil.update(x, empty)
    assert dictutil.hash(x) == before


# --- Property 2: normalize idempotence ------------------------------------------------

_NORMALIZE_MODELS = [m for m in MODELS if hasattr(m, "normalize")]
_NORMALIZE_DICTUTILS = [(m, du) for m, du in DICTUTILS if hasattr(du, "normalize")]


def _needs_mapping(params: list[inspect.Parameter]) -> bool:
    """Whether any of `params` is a required positional (i.e. a `mapping` arg to pass)."""
    return any(
        p.default is inspect.Parameter.empty and p.kind in _POSITIONAL for p in params
    )


def _normalize_model(x: TOMBase) -> None:
    """Call `x.normalize`, passing `{}` when the signature requires a mapping."""
    params = list(inspect.signature(x.normalize).parameters.values())  # bound: no self
    if _needs_mapping(params):
        x.normalize({})
    else:
        x.normalize()


def _normalize_dict(du: type[DictUtil[Any]], d: dict[str, Any]) -> None:
    """Call `du.normalize(d)`, passing `{}` when a mapping arg follows the data dict."""
    params = list(inspect.signature(du.normalize).parameters.values())
    if _needs_mapping(params[1:]):  # params[0] is the data dict itself
        du.normalize(d, {})
    else:
        du.normalize(d)


@pytest.mark.parametrize(
    "model", _NORMALIZE_MODELS, ids=[sweep_id(m) for m in _NORMALIZE_MODELS]
)
def test_normalize_idempotent(model: type[TOMBase]) -> None:
    x = build(model)
    _normalize_model(x)
    once = x.hash()
    _normalize_model(x)
    assert x.hash() == once


@pytest.mark.parametrize(
    ("model", "dictutil"),
    _NORMALIZE_DICTUTILS,
    ids=[sweep_id(du) for _, du in _NORMALIZE_DICTUTILS],
)
def test_normalize_idempotent_dictutil(
    model: type[TOMBase], dictutil: type[DictUtil[Any]]
) -> None:
    d = build(model).to_dict()
    _normalize_dict(dictutil, d)
    once = dictutil.hash(d)
    _normalize_dict(dictutil, d)
    assert dictutil.hash(d) == once


# --- Property 3: single-element merge is identity -------------------------------------

_MERGE_MODELS = [m for m in MODELS if hasattr(m, "merge_results")]
_MERGE_DICTUTILS = [(m, du) for m, du in DICTUTILS if hasattr(du, "merge_results")]


@pytest.mark.parametrize(
    "model", _MERGE_MODELS, ids=[sweep_id(m) for m in _MERGE_MODELS]
)
def test_merge_results_singleton_is_identity(model: type[TOMBase]) -> None:
    x = build(model)
    before = x.hash()
    out = model.merge_results([x])
    assert len(out) == 1
    assert out[0].hash() == before


@pytest.mark.parametrize(
    ("model", "dictutil"),
    _MERGE_DICTUTILS,
    ids=[sweep_id(du) for _, du in _MERGE_DICTUTILS],
)
def test_merge_results_singleton_is_identity_dictutil(
    model: type[TOMBase], dictutil: type[DictUtil[Any]]
) -> None:
    x = build(model).to_dict()
    before = dictutil.hash(x)
    out = dictutil.merge_results([x])
    assert len(out) == 1
    assert dictutil.hash(out[0]) == before
