"""Supporting base for `*DictUtil` siblings of the `TypedDict` models.

Provides shared I/O and model-parity hashing over the raw `TypedDict` form.
"""

from __future__ import annotations

__all__ = ["DictUtil", "register_union_discriminator"]

import types
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import (
    Any,
    ClassVar,
    Generic,
    Literal,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    overload,
)

import orjson
import ormsgpack
from pydantic import TypeAdapter
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from translator_tom.utils.hash import tomhash
from translator_tom.utils.object_base import TOMBase, _stable_repr

_TD = TypeVar("_TD", bound=Mapping[str, Any])


def _nested_models(annotation: Any) -> set[type[TOMBase]]:
    """Find the nested `TOMBase` subclasses referenced by a field annotation.

    Unwraps `Annotated`, `Optional`/unions, and `list`/`dict` containers.
    """
    found: set[type[TOMBase]] = set()

    def _visit(node: Any) -> None:
        metadata = getattr(node, "__metadata__", None)
        if metadata is not None:  # Annotated[X, ...] -> X
            _visit(node.__origin__)
            return
        if get_origin(node) is None:
            if isinstance(node, type) and issubclass(node, TOMBase):
                found.add(node)
            return
        for arg in get_args(node):
            if arg is not type(None):
                _visit(arg)

    _visit(annotation)
    return found


def _discriminator_for(annotation: Any) -> str | None:
    """Return the discriminator field name declared in an annotation's metadata, if any.

    Handles a discriminated union declared as `Annotated[A | B, Field(discriminator=...)]`,
    including when nested inside `list`/`dict`/`Optional` (as TRAPI's `workflow` is).
    """
    result: str | None = None

    def _visit(node: Any) -> None:
        nonlocal result
        metadata = getattr(node, "__metadata__", None)
        if metadata is not None:
            for meta in metadata:
                discriminator = getattr(meta, "discriminator", None)
                if isinstance(discriminator, str):
                    result = discriminator
            _visit(node.__origin__)
            return
        if get_origin(node) is None:
            return
        for arg in get_args(node):
            _visit(arg)

    _visit(annotation)
    return result


def _tag_literals(annotation: Any) -> tuple[Any, ...]:
    """Return the `Literal` value(s) of a discriminator field's annotation."""
    values = get_args(annotation)
    if not values:
        raise ValueError(
            f"Discriminator field annotation {annotation!r} is not a Literal."
        )
    return values


_ValueHasher = Callable[[Any], Any]

# element-wise containers, keyed by origin -> how to re-wrap the hashed elements
# (set-likes collapse to `frozenset`, matching `_stable_repr`'s order-independent hash).
_SEQ_WRAP: dict[Any, Callable[[Any], Any]] = {
    list: list,
    tuple: tuple,
    set: frozenset,
    frozenset: frozenset,
}


def _first_arg(node: Any) -> Any:
    """The first type argument of a generic (its element type), or `Any` if unparameterized."""
    args = get_args(node)
    return args[0] if args else Any


def _build_value_hasher(annotation: Any, resolve: _Resolver) -> _ValueHasher:
    """Build a hasher for a nested-model field's value, mirroring `_stable_repr`.

    Recurses through arbitrarily-nested `list`/`dict`/`set`/`tuple` containers to the
    model leaves, replacing each nested-model dict with `resolve(v).hash(v)` and keeping
    container types (`set`/`frozenset` -> `frozenset`, `tuple` -> `tuple`) so the
    dict-side hash matches the model-side `_stable_repr` at any nesting depth.
    """
    node = annotation
    while getattr(node, "__metadata__", None) is not None:  # strip Annotated[X, ...]
        node = node.__origin__
    origin = get_origin(node)

    if origin is Union or origin is types.UnionType:
        members = [arg for arg in get_args(node) if arg is not type(None)]
        if len(members) == 1:  # Optional[X] -> X
            return _build_value_hasher(members[0], resolve)
        # union of models: leaf, resolver discriminates by value
        return lambda v: resolve(v).hash(v)
    if origin in _SEQ_WRAP:
        wrap = _SEQ_WRAP[origin]
        inner = _build_value_hasher(_first_arg(node), resolve)
        return lambda v: wrap(inner(x) for x in v)
    if origin is dict:
        args = get_args(node)  # (key, value) or () for a bare dict
        inner = _build_value_hasher(args[-1] if args else Any, resolve)
        return lambda v: {k: inner(x) for k, x in v.items()}
    if isinstance(node, type) and issubclass(node, TOMBase):  # model leaf
        return lambda v: resolve(v).hash(v)
    return _stable_repr  # non-model scalar leaf (defensive; nested fields bottom out at models)


class DictUtil(Generic[_TD]):
    """Base for the `*DictUtil` sibling classes of the `TypedDict` models.

    A `*DictUtil` reimplements the utility methods of its Pydantic counterpart for
    the `TypedDict` form, so users can operate on plain dicts without time overhead
    for model construction/validation.

    Subclasses set `_model` (the mirrored model). It provides
    the field names/order used by `hash` and, via its field types, which fields
    hold nested models that recurse into a sibling `DictUtil` (see `_nested_fields`).
    """

    # The Pydantic model this dict mirrors; the source of truth for hashing.
    _model: ClassVar[type[TOMBase]]
    # Registry of model -> its DictUtil, populated as subclasses are defined.
    _registry: ClassVar[dict[type[TOMBase], type[DictUtil[Any]]]] = {}
    # Per-subclass cache for `_nested_fields()`.
    _nested_fields_cache: ClassVar[dict[str, _ValueHasher] | None] = None
    # Per-subclass cache for `_field_defaults()`.
    _field_defaults_cache: ClassVar[dict[str, Any] | None] = None
    # Per-subclass cache for `_adapter()` (built lazily on first validating parse).
    _adapter_cache: ClassVar[TypeAdapter[Any] | None] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register each concrete `*DictUtil` under the model it mirrors."""
        super().__init_subclass__(**kwargs)
        model = cls.__dict__.get("_model")
        if model is not None:
            DictUtil._registry[model] = cls

    ##### I/O methods #####

    @classmethod
    def _adapter(cls) -> TypeAdapter[Any]:
        """Return the cached `TypeAdapter` over this util's `TypedDict`, building it lazily."""
        cached = cls.__dict__.get("_adapter_cache")
        if cached is not None:
            return cached
        typed_dict = next(
            (
                arg
                for base in getattr(cls, "__orig_bases__", ())
                for arg in get_args(base)
            ),
            None,
        )
        if typed_dict is None:
            raise TypeError(
                f"{cls.__name__}: cannot resolve the TypedDict type parameter for validation."
            )
        adapter: TypeAdapter[Any] = TypeAdapter(typed_dict)
        cls._adapter_cache = adapter
        return adapter

    @classmethod
    def from_json(cls, json: str | bytes, validate: bool = False) -> _TD:
        """Deserialize a dict from JSON.

        With `validate=True`, data is validated using pydantic TypeAdapter and raises
        `pydantic.ValidationError` if it failes validation. The returned dict is not
        modified by the validation (extra keys preserved, etc).
        """
        data = orjson.loads(json)
        if validate:
            cls._adapter().validate_python(data)
        return cast("_TD", data)

    @overload
    @classmethod
    def to_json(cls, obj: _TD) -> bytes: ...

    @overload
    @classmethod
    def to_json(cls, obj: _TD, as_str: Literal[True]) -> str: ...

    @overload
    @classmethod
    def to_json(cls, obj: _TD, as_str: Literal[False]) -> bytes: ...

    @overload
    @classmethod
    def to_json(cls, obj: _TD, as_str: bool) -> str | bytes: ...

    @classmethod
    def to_json(cls, obj: _TD, as_str: bool = False) -> str | bytes:
        """Serialize a dict to JSON.

        Dicts are expected to already be in canonical form.
        """
        json = orjson.dumps(obj)
        if as_str:
            return json.decode()
        return json

    @classmethod
    def from_msgpack(cls, msgpack: bytes, validate: bool = False) -> _TD:
        """Deserialize a dict from MessagePack.

        With `validate=True`, data is validated using pydantic TypeAdapter and raises
        `pydantic.ValidationError` if it failes validation. The returned dict is not
        modified by the validation (extra keys preserved, etc).
        """
        data = ormsgpack.unpackb(msgpack)
        if validate:
            cls._adapter().validate_python(data)
        return cast("_TD", data)

    @classmethod
    def to_msgpack(cls, obj: _TD) -> bytes:
        """Serialize a dict to MessagePack."""
        return ormsgpack.packb(obj)

    ##### Hashing #####

    @classmethod
    def _nested_fields(cls) -> dict[str, _ValueHasher]:
        """Map each field holding nested model(s) to a value-hasher.

        Derived and cached from the mirrored model's field types: each hasher mirrors
        `_stable_repr`'s structure for that field's (possibly nested) containers,
        substituting nested-model dicts with the resolved member util's hash
        (see `_build_value_hasher` and `_nested_resolver`).
        """
        cached = cls.__dict__.get("_nested_fields_cache")
        if cached is not None:
            return cached
        mapping: dict[str, _ValueHasher] = {}
        for name, field in cls._model.model_fields.items():
            models = _nested_models(field.annotation)
            if models:
                resolve = cls._nested_resolver(name, field, models)
                mapping[name] = _build_value_hasher(field.annotation, resolve)
        cls._nested_fields_cache = mapping
        return mapping

    @classmethod
    def _util_for(cls, field_name: str, model: type[TOMBase]) -> type[DictUtil[Any]]:
        """Return the registered `DictUtil` for `model`, or raise if none exists."""
        util = cls._registry.get(model)
        if util is None:
            raise LookupError(
                f"{cls.__name__}: field {field_name!r} holds {model.__name__}, but no "
                f"DictUtil is registered for it (define {model.__name__}DictUtil)."
            )
        return util

    @classmethod
    def _nested_resolver(
        cls, field_name: str, field: FieldInfo, models: set[type[TOMBase]]
    ) -> _Resolver:
        """Build the resolver mapping a nested field's value to the util that hashes it.

        Single-model fields resolve to a constant util. Union fields resolve per
        element: by discriminator tag for a pydantic tagged union, otherwise via a
        discriminator registered with `register_union_discriminator`.
        """
        if len(models) == 1:
            (model,) = models
            return _ConstResolver(cls._util_for(field_name, model))
        discriminator = (
            field.discriminator
            if isinstance(field.discriminator, str)
            else _discriminator_for(field.annotation)
        )
        if discriminator is not None:
            by_tag: dict[Any, type[DictUtil[Any]]] = {}
            for model in models:
                util = cls._util_for(field_name, model)
                for tag in _tag_literals(model.model_fields[discriminator].annotation):
                    by_tag[tag] = util
            return _TagResolver(discriminator, by_tag)
        discriminate = _UNION_DISCRIMINATORS.get(frozenset(models))
        if discriminate is None:
            raise LookupError(
                f"{cls.__name__}: field {field_name!r} is a union of "
                f"{sorted(m.__name__ for m in models)} with no discriminator; register "
                "one with register_union_discriminator()."
            )
        return _StructuralResolver(
            discriminate, {model: cls._util_for(field_name, model) for model in models}
        )

    @classmethod
    def _hash_field(cls, key: str, value: Any) -> Any:
        """Produce the stable representation of one declared field for hashing."""
        hasher = cls._nested_fields().get(key)
        if hasher is None or value is None:
            return _stable_repr(value)
        return hasher(value)

    @classmethod
    def _field_defaults(cls) -> dict[str, Any]:
        """Map each model field to its default (for keys omitted from a dict)."""
        cached = cls.__dict__.get("_field_defaults_cache")
        if cached is not None:
            return cached
        # to_dict omits default-valued fields; restoring the default lets a dict hash
        # like the model, whose hash reads live (always-present) field values.
        defaults: dict[str, Any] = {}
        for name, field in cls._model.model_fields.items():
            default = field.get_default(call_default_factory=True)
            defaults[name] = None if default is PydanticUndefined else default
        cls._field_defaults_cache = defaults
        return defaults

    @classmethod
    def _default(cls, field_name: str) -> Any:
        """Return the mirrored model's default for `field_name` (its model attribute name)."""
        return cls._field_defaults()[field_name]

    @classmethod
    def hash(cls, obj: _TD) -> str:
        """Hash the dict into a hex string, matching the corresponding model's `hash()`.

        Hashes only declared fields (not extra keys), keyed by the model's field
        names in definition order, so a dict and its equivalent model hash equally.
        Fields omitted from the dict fall back to their model default (see
        `_field_defaults`), mirroring the model whose defaults are always live.
        """
        defaults = cls._field_defaults()
        return tomhash(
            (
                cls._model.__name__,
                *(
                    (key, cls._hash_field(key, obj.get(key, defaults[key])))
                    for key in cls._model.model_fields
                ),
            )
        )


# A resolver maps a nested field's dict value to the `DictUtil` that hashes it.
_Resolver = Callable[[Any], "type[DictUtil[Any]]"]
# A structural-union discriminator maps a raw dict to its concrete member model.
_Discriminator = Callable[[Mapping[str, Any]], type[TOMBase]]


@dataclass
class _ConstResolver:
    """Resolver for a single-model field: always the one util."""

    util: type[DictUtil[Any]]

    def __call__(self, value: Any) -> type[DictUtil[Any]]:
        """Return the field's util, ignoring `value`."""
        return self.util


@dataclass
class _TagResolver:
    """Resolver for a pydantic tagged union: pick the util by the discriminator value."""

    tag_field: str
    by_tag: dict[Any, type[DictUtil[Any]]]

    def __call__(self, value: Any) -> type[DictUtil[Any]]:
        """Return the util for `value`'s discriminator tag."""
        return self.by_tag[value[self.tag_field]]


@dataclass
class _StructuralResolver:
    """Resolver for a structural union: discriminate the dict, then map model -> util."""

    discriminate: _Discriminator
    by_model: dict[type[TOMBase], type[DictUtil[Any]]]

    def __call__(self, value: Any) -> type[DictUtil[Any]]:
        """Return the util for the model `discriminate` selects for `value`."""
        return self.by_model[self.discriminate(value)]


_UNION_DISCRIMINATORS: dict[frozenset[type[TOMBase]], _Discriminator] = {}


def register_union_discriminator(
    members: Iterable[type[TOMBase]], discriminate: _Discriminator
) -> None:
    """Register how to resolve a structural (non-tagged) union of models from a raw dict.

    `discriminate` receives the raw dict and returns the concrete member model class.
    Needed only for unions without a pydantic discriminator (e.g. `QueryGraph` vs
    `PathfinderQueryGraph`); tagged unions are resolved automatically.
    """
    _UNION_DISCRIMINATORS[frozenset(members)] = discriminate
