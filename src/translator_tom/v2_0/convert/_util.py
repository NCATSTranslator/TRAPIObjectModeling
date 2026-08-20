"""Supporting core for the TRAPI 1.6 → 2.0 model converter.

Provides the `@singledispatch` `up_version` generic
plus the shared helpers the per-model registration modules build on.
"""

from __future__ import annotations

__all__ = ["up_version"]

import types
from functools import singledispatch
from typing import TYPE_CHECKING, Any, TypeVar, Union, get_args, get_origin

from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBase

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

_Model = TypeVar("_Model", bound=TOMBase)

_SEQUENCE_ORIGINS = (list, set, tuple, frozenset)

# The 1.6 attribute_type_ids that 2.0 promotes to required top-level Edge fields.
KNOWLEDGE_LEVEL_ATTRIBUTE_ID = Biolink("knowledge_level")
AGENT_TYPE_ATTRIBUTE_ID = Biolink("agent_type")

# `not_provided` is a permissible value of both biolink KnowledgeLevelEnum and
# AgentTypeEnum; the fallback when a 1.6 edge carries no KL/AT attribute.
DEFAULT_KNOWLEDGE_LEVEL = "not_provided"
DEFAULT_AGENT_TYPE = "not_provided"


@singledispatch
def up_version(obj: TOMBase, **kwargs: Any) -> TOMBase:
    """Upgrade a TRAPI 1.6 TOM model to its TRAPI 2.0 equivalent.

    Dispatches on the 1.6 model type. Structurally-unchanged models
    re-parse into same-named 2.0 twin.
    `**kwargs` passes through recursion for forward compatibility.
    """
    return _build(_v2_equivalent(type(obj)), obj.to_dict())


def _v2_equivalent(source: type[TOMBase]) -> type[TOMBase]:
    """The TRAPI 2.0 model class sharing `source`'s name."""
    # lazy import: avoids a partially-initialized cycle (convert loads during v2_0 init)
    from translator_tom import v2_0  # noqa: PLC0415

    twin = getattr(v2_0, source.__name__, None)
    if twin is None:
        raise NotImplementedError(
            f"No TRAPI 2.0 equivalent is exported for {source.__name__!r}."
        )
    return twin


def _build(model_cls: type[_Model], data: dict[str, Any]) -> _Model:
    """Validate converted `data` into `model_cls`, first pruning empty arrays.

    `to_dict()` emits empty arrays for 1.6 fields that held them, but TRAPI 2.0 forbids
    empty arrays on its minItems:1 properties (an absent property is the canonical
    "no data"), so those must be dropped before validation.
    """
    return model_cls.from_dict(_prune_empty_arrays(model_cls, data))


def _prune_empty_arrays(
    model_cls: type[TOMBase], data: dict[str, Any]
) -> dict[str, Any]:
    """Recursively drop optional fields whose value is an empty array.

    Only OPTIONAL target fields are dropped, so genuinely-empty required data (e.g. an
    Attribute whose `value` is `[]`) and valid empty containers on required fields are
    preserved for pydantic to validate. Recurses into nested models, so deeply-nested
    empties (e.g. a MetaEdge inside a MetaKnowledgeGraph) are handled too.
    """
    fields = model_cls.model_fields
    pruned: dict[str, Any] = {}
    for key, value in data.items():
        field = fields.get(key)
        if field is None:  # extra (undeclared) property: opaque, leave as-is
            pruned[key] = value
            continue
        if value == [] and not field.is_required():
            continue
        model, container = _nested_model(field.annotation)
        pruned[key] = _prune_nested(model, container, value) if model else value
    return pruned


def _prune_nested(model: type[TOMBase], container: str, value: Any) -> Any:
    """Apply `_prune_empty_arrays` to the nested-model dict(s) held in `value`."""
    if container == "model" and isinstance(value, dict):
        return _prune_empty_arrays(model, value)
    if container == "list" and isinstance(value, list):
        return [
            _prune_empty_arrays(model, item) if isinstance(item, dict) else item
            for item in value
        ]
    if container == "dict" and isinstance(value, dict):
        return {
            key: _prune_empty_arrays(model, item) if isinstance(item, dict) else item
            for key, item in value.items()
        }
    return value


def _nested_model(annotation: Any) -> tuple[type[TOMBase] | None, str]:
    """Resolve `annotation` to its single nested model and container kind.

    Returns `(model, "model" | "list" | "dict")`, or `(None, "")` when the field holds no
    single nested model (a scalar, or a multi-member union we don't recurse into).
    """
    node = annotation
    while getattr(node, "__metadata__", None) is not None:  # unwrap Annotated[X, …]
        node = node.__origin__
    origin = get_origin(node)
    if origin is Union or origin is types.UnionType:
        members = [arg for arg in get_args(node) if arg is not type(None)]
        return _nested_model(members[0]) if len(members) == 1 else (None, "")
    if origin in _SEQUENCE_ORIGINS:
        args = get_args(node)
        return (args[0], "list") if args and _is_model(args[0]) else (None, "")
    if origin is dict:
        args = get_args(node)  # (key, value) for a parameterized dict
        return (args[-1], "dict") if args and _is_model(args[-1]) else (None, "")
    return (node, "model") if _is_model(node) else (None, "")


def _is_model(annotation: Any) -> bool:
    """Whether `annotation` is a TOMBase subclass."""
    return isinstance(annotation, type) and issubclass(annotation, TOMBase)


def _binding_dedup(ids: Iterable[str]) -> list[str]:
    """Order-stable de-duplication of binding ids."""
    return list(dict.fromkeys(ids))


def _collapse_bindings(
    binding_map: Mapping[str, list[Any]],
) -> dict[str, dict[str, list[str]]] | None:
    """Collapse a 1.6 `{key: [binding, …]}` map into 2.0 `{key: {"ids": […]}}`.

    Each binding's single `id` is unioned into the target binding's `ids`. Keys whose
    bindings yield no ids are dropped; an empty result is `None` (the container is
    optional in 2.0).
    """
    collapsed: dict[str, dict[str, list[str]]] = {}
    for key, bindings in binding_map.items():
        ids = _binding_dedup(binding.id for binding in bindings)
        if ids:
            collapsed[key] = {"ids": ids}

    return collapsed or None
