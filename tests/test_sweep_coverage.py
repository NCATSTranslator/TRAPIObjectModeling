"""DictUtil registration-coverage sweep.

Asserts the model<->DictUtil registry is complete and internally consistent, so a
model that silently ships without its DictUtil sibling (as ``AsyncQuery`` once did)
fails loudly here rather than only at runtime. New models/DictUtils are covered
automatically via the shared ``_sweep_helpers`` harness.
"""

from __future__ import annotations

from typing import Any

import pytest
from _sweep_helpers import DICTUTILS, MODELS

from translator_tom import TOMBase
from translator_tom.utils.dict_util_base import DictUtil

# Models that legitimately have no DictUtil sibling. Each entry MUST be justified: a
# normal serializable model missing its DictUtil is a BUG to fix, not to allow-list.
# TRAPI 2.0 collapsed Base/PathfinderQueryGraph into a single concrete QueryGraph, so the
# former abstract-base exemption no longer applies; every public model now has a DictUtil.
EXPECTED_NO_DICTUTIL: set[type] = set()


def test_forward_coverage() -> None:
    """Every public model has a DictUtil, except the documented allow-set.

    Equality (not subset) so a newly-missing DictUtil and a stale allow-set entry
    that has since gained one both fail here.
    """
    uncovered = set(MODELS) - set(DictUtil._registry)
    assert uncovered == EXPECTED_NO_DICTUTIL


@pytest.mark.parametrize(
    ("model", "dictutil"),
    DICTUTILS,
    ids=[du.__name__ for _, du in DICTUTILS],
)
def test_dictutil_model_is_own_and_valid(
    model: type[TOMBase], dictutil: type[DictUtil[Any]]
) -> None:
    """Each DictUtil sets its own `_model` (not inherited) to a real TOMBase subclass."""
    own_model = dictutil.__dict__.get("_model")
    assert own_model is model  # registered under its own `_model`, not a base's
    assert isinstance(own_model, type) and issubclass(own_model, TOMBase)


def test_registry_is_one_to_one() -> None:
    """No two models share a DictUtil; the registry maps each model to a distinct util.

    Read live (not the ``DICTUTILS`` snapshot): other test modules register throwaway
    DictUtils into the global registry, so any count check must come from one source.
    """
    registry = DictUtil._registry
    assert len(set(registry.values())) == len(registry)


@pytest.mark.parametrize(
    ("model", "dictutil"),
    DICTUTILS,
    ids=[du.__name__ for _, du in DICTUTILS],
)
def test_dictutil_adapter_builds(
    model: type[TOMBase], dictutil: type[DictUtil[Any]]
) -> None:
    """Each DictUtil resolves its TypedDict into a TypeAdapter without raising.

    Generic guard for the forward-ref/adapter bug class.
    """
    assert dictutil._adapter() is not None
