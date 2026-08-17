from __future__ import annotations

__all__ = ["TOMBase"]

from typing import Any, ClassVar, Literal, cast, overload

import orjson
import ormsgpack
from pydantic import BaseModel, ConfigDict, JsonValue
from typing_extensions import Self, override

from translator_tom.utils.hash import tomhash, tomhash_int


def _stable_repr(val: Any) -> Any:
    """Recursively replace TOMBaseObjects with their hash().

    Avoids instabilities caused by stablehash's access of TOMBaseObject fields via __getstate__.
    """
    if isinstance(val, TOMBase):
        return val.hash()
    if isinstance(val, dict):
        return {k: _stable_repr(v) for k, v in cast("dict[Any, Any]", val).items()}
    if isinstance(val, list):
        return [_stable_repr(v) for v in cast("list[Any]", val)]
    if isinstance(val, tuple):
        return tuple(_stable_repr(v) for v in cast("tuple[Any, ...]", val))
    if isinstance(val, (set, frozenset)):
        return frozenset(_stable_repr(v) for v in cast("set[Any]", val))
    return val


class TOMBase(BaseModel):
    """A base class handling (de)serialization and providing method requirements."""

    # Set fast defaults, subclasses inherit and override as needed.
    model_config: ClassVar[ConfigDict] = ConfigDict(
        defer_build=False,
        validate_assignment=False,
        revalidate_instances="never",
        validate_default=False,
        protected_namespaces=(),
        extra="allow",
        use_attribute_docstrings=True,  # field docstrings -> schema descriptions
    )

    ###### I/O methods #####

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> Self:
        """Deserialize an instance from a python dictionary representation."""
        return cls.model_validate(obj)

    def to_dict(self) -> dict[str, Any]:
        """Serialize an instance to python dictionary representation.

        Excludes serializing default and None fields to save space.
        """
        return self.model_dump(mode="json", exclude_none=True, exclude_defaults=True)

    @classmethod
    def from_json(cls, json: str | bytes) -> Self:
        """Deserialize an instance from JSON."""
        # orjson.loads + model_validate beats model_validate_json by 10-30% due to TOM
        # complexities: extra="allow" everywhere, deep model recursion, Any fields, etc.
        # Revisit as pydantic updates
        return cls.model_validate(orjson.loads(json))

    @overload
    def to_json(self) -> bytes: ...

    @overload
    def to_json(self, as_str: Literal[True]) -> str: ...

    @overload
    def to_json(self, as_str: Literal[False]) -> bytes: ...

    @overload
    def to_json(self, as_str: bool) -> str | bytes: ...

    def to_json(self, as_str: bool = False) -> str | bytes:
        """Serialize an instance to json.

        Uses pydantic's own json serialization because it appears faster in testing.
        """
        # __pydantic_serializer__.to_json returns bytes directly
        json = self.__pydantic_serializer__.to_json(
            self, exclude_none=True, exclude_defaults=True
        )
        if as_str:
            return json.decode()
        return json

    @classmethod
    def from_msgpack(cls, msgpack: bytes) -> Self:
        """Deserialize an instance from MessagePack."""
        return cls.model_validate(ormsgpack.unpackb(msgpack))

    def to_msgpack(self) -> bytes:
        """Serialize an instance to MessagePack."""
        # ormsgpack can serialize pydantic directly
        return ormsgpack.packb(self, option=ormsgpack.OPT_SERIALIZE_PYDANTIC)

    ##### Misc. #####

    @property
    def extra_dict(self) -> dict[str, JsonValue]:
        """Return the model extra fields, or a fresh empty dict if none are present.

        Don't mutate the returned dict; use .extra_set() to add extras. When the model
        has no extras this returns a throwaway empty dict, so mutating it has no effect.
        """
        return self.__pydantic_extra__ or {}

    def extra_get(self, key: str, default: Any = None) -> Any:
        """Get an extra field or the given default, if extra is allowed."""
        if self.__pydantic_extra__ is None:
            raise ValueError(f"{type(self)} does not allow extra values.")
        return self.__pydantic_extra__.get(key, default)

    def extra_set(self, key: str, value: JsonValue) -> None:
        """Set an extra field to the given value, if extra is allowed."""
        if self.__pydantic_extra__ is None:
            raise ValueError(f"{type(self)} does not allow extra values.")
        self.__pydantic_extra__[key] = value

    def _hash_repr(self) -> object:
        """Build the stable hashable value shared by hash() and __hash__.

        Subclasses override this (not hash()) so both the string hash() and the
        int __hash__ derive from the same input.
        """
        # NOTE: only hashes fields that are not extra
        return (
            self.__class__.__name__,
            *(
                (key, _stable_repr(val))
                for key, val in self.__dict__.items()
                if key in self.__pydantic_fields__
            ),
        )

    def hash(self) -> str:
        """Hash the object into a hex string."""
        return tomhash(self._hash_repr())

    @override
    def __hash__(self) -> int:
        # derive int directly from digest, skipping the base64 round-trip
        return tomhash_int(self._hash_repr())

    @override
    def __eq__(self, other: object) -> bool:
        """Check for equality between self an other, using hashes."""
        return bool(
            isinstance(other, TOMBase)
            and isinstance(other, type(self))
            and self.hash() == other.hash()
        )
