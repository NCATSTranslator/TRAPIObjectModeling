"""Supporting core for the TRAPI 1.6 → 2.0 converter (model and dict layers).

Both layers share one set of pure `dict -> dict` upgrade transforms: the model layer
`up_version(obj)` builds a 2.0 model from `transform(obj.to_dict())`; the dict layer
`dict_up_version(data, source)` applies the same transform to a raw dict and stops.
Transforms are registered once, for both layers, with `@register(source, target)`.
"""

from __future__ import annotations

__all__ = ["dict_up_version", "up_version"]

import types
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin, overload

from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBase

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from translator_tom import v1_6, v2_0
    from translator_tom.v2_0 import model_dicts as v2_0_dicts

_Data = dict[str, Any]
_Transform = Callable[..., _Data]

_SEQUENCE_ORIGINS = (list, set, tuple, frozenset)

# The 1.6 attribute_type_ids that 2.0 promotes to required top-level Edge fields.
KNOWLEDGE_LEVEL_ATTRIBUTE_ID = Biolink("knowledge_level")
AGENT_TYPE_ATTRIBUTE_ID = Biolink("agent_type")

# `not_provided` is a permissible value of both biolink KnowledgeLevelEnum and
# AgentTypeEnum; the fallback when a 1.6 edge carries no KL/AT attribute.
DEFAULT_KNOWLEDGE_LEVEL = "not_provided"
DEFAULT_AGENT_TYPE = "not_provided"

# Populated by `register`: source 1.6 model -> its dict transform / its 2.0 target class.
_TRANSFORMS: dict[type[TOMBase], _Transform] = {}
_TARGETS: dict[type[TOMBase], type[TOMBase] | None] = {}


# Reasonable overload set for commonly-used items, the rest have to be cast()
@overload
def up_version(obj: v1_6.Response, **kwargs: Any) -> v2_0.Response: ...
@overload
def up_version(obj: v1_6.AsyncQuery, **kwargs: Any) -> v2_0.AsyncQuery: ...
@overload
def up_version(obj: v1_6.Query, **kwargs: Any) -> v2_0.Query: ...
@overload
def up_version(obj: v1_6.Message, **kwargs: Any) -> v2_0.Message: ...
@overload
def up_version(obj: v1_6.KnowledgeGraph, **kwargs: Any) -> v2_0.KnowledgeGraph: ...
@overload
def up_version(obj: v1_6.QueryGraph, **kwargs: Any) -> v2_0.QueryGraph: ...
@overload
def up_version(obj: v1_6.Result, **kwargs: Any) -> v2_0.Result: ...
@overload
def up_version(obj: v1_6.Analysis, **kwargs: Any) -> v2_0.Analysis: ...
@overload
def up_version(obj: v1_6.Edge, **kwargs: Any) -> v2_0.Edge: ...
@overload
def up_version(obj: v1_6.QEdge, **kwargs: Any) -> v2_0.QEdge: ...
@overload
def up_version(obj: v1_6.QualifierConstraint, **kwargs: Any) -> dict[str, str]: ...
@overload
def up_version(obj: TOMBase, **kwargs: Any) -> TOMBase: ...
def up_version(obj: TOMBase, **kwargs: Any) -> Any:
    """Upgrade a TRAPI 1.6 TOM model to its TRAPI 2.0 equivalent.

    Dispatches on the 1.6 model type; structurally-unchanged models re-parse into their
    same-named 2.0 twin. Equivalent to the dict converter plus a `from_dict`.
    `**kwargs` passes through the recursion for forward compatibility.

    Overloads give the precise 2.0 type for the inputs handled standalone (Response,
    Query, AsyncQuery, Message, KnowledgeGraph, QueryGraph, Result, Analysis, Edge,
    QEdge); any other source is typed `TOMBase` and needs a cast to its concrete 2.0
    class.
    """
    source = type(obj)
    data = dict_up_version(obj.to_dict(), source, **kwargs)
    target = _target_for(source)
    return target.from_dict(data) if target is not None else data


def register(
    source: type[TOMBase], target: type[TOMBase] | None
) -> Callable[[_Transform], _Transform]:
    """Register a pure `dict -> dict` upgrade transform under `source`, for both layers.

    `target` is the 2.0 model class the transform yields, or `None` when it yields a bare
    mapping (e.g. `QualifierConstraint` → `{type_id: value}`, which stays a dict).
    """

    def decorator(transform: _Transform) -> _Transform:
        _TRANSFORMS[source] = transform
        _TARGETS[source] = target
        return transform

    return decorator


@overload
def dict_up_version(
    data: _Data, source: type[v1_6.Response], **kwargs: Any
) -> v2_0_dicts.ResponseDict: ...
@overload
def dict_up_version(
    data: _Data, source: type[v1_6.AsyncQuery], **kwargs: Any
) -> v2_0_dicts.AsyncQueryDict: ...
@overload
def dict_up_version(
    data: _Data, source: type[v1_6.Query], **kwargs: Any
) -> v2_0_dicts.QueryDict: ...
@overload
def dict_up_version(
    data: _Data, source: type[v1_6.Message], **kwargs: Any
) -> v2_0_dicts.MessageDict: ...
@overload
def dict_up_version(
    data: _Data, source: type[v1_6.KnowledgeGraph], **kwargs: Any
) -> v2_0_dicts.KnowledgeGraphDict: ...
@overload
def dict_up_version(
    data: _Data, source: type[v1_6.QueryGraph], **kwargs: Any
) -> v2_0_dicts.QueryGraphDict: ...
@overload
def dict_up_version(
    data: _Data, source: type[v1_6.Result], **kwargs: Any
) -> v2_0_dicts.ResultDict: ...
@overload
def dict_up_version(
    data: _Data, source: type[v1_6.Analysis], **kwargs: Any
) -> v2_0_dicts.AnalysisDict: ...
@overload
def dict_up_version(
    data: _Data, source: type[v1_6.Edge], **kwargs: Any
) -> v2_0_dicts.EdgeDict: ...
@overload
def dict_up_version(
    data: _Data, source: type[v1_6.QEdge], **kwargs: Any
) -> v2_0_dicts.QEdgeDict: ...
@overload
def dict_up_version(data: _Data, source: type[TOMBase], **kwargs: Any) -> _Data: ...
def dict_up_version(data: _Data, source: type[TOMBase], **kwargs: Any) -> Any:
    """Upgrade a raw TRAPI 1.6 dict to the 2.0 dict shape, without constructing models.

    `source` is the 1.6 model class that `data` represents. Applies the shared transform
    (if the source changed) and prunes to canonical 2.0 form; unchanged sources pass
    through with only the prune.

    Overloads give the precise 2.0 `*Dict` type for the sources handled standalone
    (Response, Query, AsyncQuery, Message, KnowledgeGraph, QueryGraph, Result, Analysis,
    Edge, QEdge); any other source is typed `dict[str, Any]` and needs a cast to its
    concrete 2.0 `*Dict`.
    """
    transform = _TRANSFORMS.get(source)
    if transform is not None:
        data = transform(data, **kwargs)
    target = _target_for(source)
    return _prune(target, data) if target is not None else data


def _target_for(model: type[TOMBase]) -> type[TOMBase] | None:
    """The 2.0 target for a 1.6 source: the registered target, else the same-named twin."""
    if model in _TARGETS:
        return _TARGETS[model]
    return _v2_equivalent(model)


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


def _prune(model_cls: type[TOMBase], data: dict[str, Any]) -> dict[str, Any]:
    """Recursively canonicalize a 2.0-shaped dict: drop nulls and empty optional arrays.

    TRAPI 2.0 forbids `null` (absent is "no data") and forbids empty arrays on its
    minItems:1 properties. Dropping nulls mirrors `to_dict`'s `exclude_none`, so the dict
    layer's output matches the model layer's. Empty arrays are dropped only for OPTIONAL
    target fields, so genuinely-empty required data (e.g. an Attribute whose `value` is
    `[]`) is preserved for pydantic to validate. Recurses into nested models.
    """
    fields = model_cls.model_fields
    pruned: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:  # 2.0 forbids null (matches to_dict's exclude_none)
            continue
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
    """Apply `_prune` to the nested-model dict(s) held in `value`."""
    if container == "model" and isinstance(value, dict):
        return _prune(model, value)
    if container == "list" and isinstance(value, list):
        return [
            _prune(model, item) if isinstance(item, dict) else item for item in value
        ]
    if container == "dict" and isinstance(value, dict):
        return {
            key: _prune(model, item) if isinstance(item, dict) else item
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
    binding_map: Mapping[str, list[_Data]],
) -> dict[str, dict[str, list[str]]] | None:
    """Collapse a 1.6 `{key: [binding, …]}` dict map into 2.0 `{key: {"ids": […]}}`.

    Each binding dict's single `id` is unioned into the target binding's `ids`. Keys
    whose bindings yield no ids are dropped; an empty result is `None` (the container is
    optional in 2.0).
    """
    collapsed: dict[str, dict[str, list[str]]] = {}
    for key, bindings in binding_map.items():
        ids = _binding_dedup(binding["id"] for binding in bindings)
        if ids:
            collapsed[key] = {"ids": ids}

    return collapsed or None
