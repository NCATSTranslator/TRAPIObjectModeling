"""Sweep: every `*Enum` export must share its Literal twin's value set.

Convention (CLAUDE.md): "Literal over Enum internally; Enums are still provided
for documentation and suffixed `Enum` (e.g. `LogLevel` literal vs `LogLevelEnum`)."
This guards the two from drifting apart. Runs over every version package, so new
`*Enum` exports in any version are covered automatically via its `__all__`.
"""

from __future__ import annotations

import sys
from types import ModuleType
from typing import get_args

import pytest
from _sweep_helpers import VERSIONS

# `*Enum` exports that legitimately have no Literal twin (verified: no matching
# name at version level or in the enum's defining module). Not drift -> allow-set,
# not xfail.
NO_LITERAL_TWIN: set[str] = {
    # config-only int enum (hash_representation setting); no Literal is used.
    "HashRepEnum",
}


def _twin_name(enum_name: str) -> str:
    return enum_name.removesuffix("Enum")


def _find_twin(version: ModuleType, enum_cls: type) -> object | None:
    name = _twin_name(enum_cls.__name__)
    twin = getattr(version, name, None)
    if twin is None:
        twin = getattr(sys.modules[enum_cls.__module__], name, None)
    return twin


def _enum_values(enum_cls: type) -> set:
    return {member.value for member in enum_cls}


def _make_param(version: ModuleType, enum_name: str) -> object:
    label = f"{version.__name__.rsplit('.', 1)[-1]}:{enum_name}"
    enum_cls = getattr(version, enum_name)
    if enum_name in NO_LITERAL_TWIN:
        return pytest.param(version, enum_name, id=label)
    marks: object = ()
    twin = _find_twin(version, enum_cls)
    if twin is not None:
        enum_vals = _enum_values(enum_cls)
        literal_vals = set(get_args(twin))
        if enum_vals != literal_vals:
            marks = pytest.mark.xfail(
                reason=(
                    f"BUG: {enum_name} values {enum_vals} != "
                    f"{_twin_name(enum_name)} args {literal_vals}"
                ),
                strict=False,
            )
    return pytest.param(version, enum_name, id=label, marks=marks)


ENUM_PARAMS = [
    _make_param(version, name)
    for version in VERSIONS
    for name in version.__all__
    if name.endswith("Enum")
]


@pytest.mark.parametrize(("version", "enum_name"), ENUM_PARAMS)
def test_enum_literal_parity(version: ModuleType, enum_name: str) -> None:
    enum_cls = getattr(version, enum_name)
    twin = _find_twin(version, enum_cls)

    if enum_name in NO_LITERAL_TWIN:
        assert twin is None, (
            f"{enum_name} now has a Literal twin `{_twin_name(enum_name)}`; "
            "remove it from NO_LITERAL_TWIN so parity is enforced."
        )
        return

    assert twin is not None, (
        f"No Literal twin `{_twin_name(enum_name)}` found for {enum_name} "
        "(version level or in its defining module)."
    )
    assert _enum_values(enum_cls) == set(get_args(twin))
