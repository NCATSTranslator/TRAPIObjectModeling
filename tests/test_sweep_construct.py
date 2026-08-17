"""Registry-driven construct-vs-validate hash + `.new()` validity sweep.

Two cross-cutting invariants over every model from `_sweep_helpers`:

1. Validated construction and `model_construct` agree on the identity hash for
   equivalent input. `.new()` helpers and internal fast paths build via
   `model_construct` (no validation); a silent coercion during validation (e.g.
   int -> float) would change `.hash()` and split identity from the validated form.
2. Every no-required-arg `.new()` classmethod yields a schema-valid instance:
   `model_validate(inst.to_dict())` must not raise and must preserve the hash. This
   guards the class of bug where `AsyncQuery.new()` once produced an instance missing
   its required `callback`.

Intentional overlap with the round-trip sweep (its `from_dict` leg also validates) is
fine; the focus here is construct-vs-validate hash equivalence and `.new()` validity.
"""

from __future__ import annotations

import inspect

import pytest
from _sweep_helpers import MODELS, build

from translator_tom import TOMBase

# Models the generic harness can't build-and-revalidate (harness limitation, not a
# product bug): `build` fills required fields with type-correct dummies, and a stricter
# field constraint rejects the dummy on the validating (`model_validate`) leg. Mirrors
# the round-trip sweep's skip set, keyed by class name.
SKIP: dict[str, str] = {
    # LogEntry.timestamp is Field(pattern=ISO-8601); the dummy "x" can't match it.
    "LogEntry": "harness: LogEntry.timestamp requires an ISO-8601 string; dummy 'x' fails the pattern",
    # AsyncQueryStatusResponse has a required logs: list[LogEntry] -> same pattern failure.
    "AsyncQueryStatusResponse": "harness: nested required LogEntry.timestamp requires an ISO-8601 string; dummy 'x' fails the pattern",
    # PathfinderQueryGraph.paths is Field(min_length=1); the dummy builds an empty {} dict.
    "PathfinderQueryGraph": "harness: PathfinderQueryGraph.paths requires min_length=1; dummy builds an empty dict",
}

# Real product bugs: validation silently changes the identity hash. None found.
XFAIL: dict[str, str] = {}


def _marks(name: str) -> list[pytest.MarkDecorator]:
    marks: list[pytest.MarkDecorator] = []
    if name in SKIP:
        marks.append(pytest.mark.skip(reason=SKIP[name]))
    if name in XFAIL:
        marks.append(pytest.mark.xfail(reason=XFAIL[name], strict=False))
    return marks


CONSTRUCT_PARAMS = [pytest.param(m, marks=_marks(m.__name__)) for m in MODELS]


@pytest.mark.parametrize("model", CONSTRUCT_PARAMS, ids=[m.__name__ for m in MODELS])
def test_construct_matches_validated_hash(model: type[TOMBase]) -> None:
    """`model_construct` and validated construction agree on the identity hash.

    Validation/coercion of a `model_construct`ed instance's own data must not change
    its `.hash()` (catches int/float-style coercion drift).
    """
    bare = build(model)
    validated = type(bare).model_validate(bare.to_dict())
    assert validated.hash() == bare.hash()


def _new_required_params(model: type[TOMBase]) -> list[inspect.Parameter] | None:
    """Required params of `model.new` (cls excluded), or None if it has no `.new` classmethod."""
    raw = inspect.getattr_static(model, "new", None)
    if not isinstance(raw, classmethod):
        return None
    sig = inspect.signature(model.new)
    return [
        p
        for p in sig.parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    ]


NEW_MODELS = [m for m in MODELS if _new_required_params(m) is not None]


@pytest.mark.parametrize("model", NEW_MODELS, ids=[m.__name__ for m in NEW_MODELS])
def test_new_yields_valid_instance(model: type[TOMBase]) -> None:
    """`.new()` produces a schema-valid, re-validatable instance with a stable hash.

    Required `.new` args (e.g. `AsyncQuery.new(callback)`) are supplied a dummy "x".
    """
    params = _new_required_params(model)
    assert params is not None  # NEW_MODELS is prefiltered to models that have `.new`
    args = ["x"] * sum(1 for p in params if p.kind is not p.KEYWORD_ONLY)
    kwargs = {p.name: "x" for p in params if p.kind is p.KEYWORD_ONLY}
    inst = model.new(*args, **kwargs)
    revalidated = type(inst).model_validate(inst.to_dict())
    assert revalidated.hash() == inst.hash()
