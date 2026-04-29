from typing import Any, ClassVar, Literal, Self, cast, overload, override

import ormsgpack
from pydantic import BaseModel, ConfigDict

from translator_tom.utils.hash import tomhash, tomhash_to_int


def _stable_repr(val: Any) -> Any:
    """Recursively replace TOMBaseObjects with their hash().

    Avoids instabilities caused by stablehash's access of TOMBaseObject fields via __getstate__.
    """
    if isinstance(val, TOMBaseObject):
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


class TOMBaseObject(BaseModel):
    """A base class handling (de)serialization and providing method requirements."""

    # Set fast defaults, subclasses inherit and override as needed.
    model_config: ClassVar[ConfigDict] = ConfigDict(
        defer_build=False,
        validate_assignment=False,
        revalidate_instances="never",
        validate_default=False,
        protected_namespaces=(),
    )

    ###### I/O methods #####

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> Self:
        """Deserialize an instance from a python dictionary representation."""
        return cls.model_validate(obj)

    def to_dict(self) -> dict[str, Any]:
        """Serialize an instance to python dictionary representation."""
        return self.model_dump(mode="json")

    @classmethod
    def from_json(cls, json: str | bytes) -> Self:
        """Deserialize an instance from JSON."""
        # NOTE: Outperforms orjson for larger objects due to single Rust pass
        return cls.model_validate_json(json)

    @overload
    def to_json(self) -> str: ...

    @overload
    def to_json(self, as_str: Literal[True]) -> str: ...

    @overload
    def to_json(self, as_str: Literal[False]) -> bytes: ...

    def to_json(self, as_str: bool = False) -> str | bytes:
        """Serialize an instance to json.

        Uses pydantic's own json serialization because it appears faster in testing.
        """
        # __pydantic_serializer__.to_json returns bytes directly
        json = self.__pydantic_serializer__.to_json(self)
        if as_str:
            return json.decode()
        return json

    @classmethod
    def from_msgpack(cls, msgpack: bytes) -> Self:
        """Deserialize an instance from MessagePack."""
        return cls.model_validate(ormsgpack.unpackb(msgpack))

    def to_msgpack(self) -> bytes:
        """Serialize an instance to MessagePack."""
        return ormsgpack.packb(
            self.__pydantic_serializer__.to_python(self, mode="json")
        )

    ##### Misc. #####

    def __getitem__(self, key: str) -> Any:
        """Get an extra item, if present."""
        if self.__pydantic_extra__ is None:
            raise ValueError(f"{type(self)} does not allow extra values.")
        return self.__pydantic_extra__[key]

    def get(self, key: str, default: Any | None) -> Any:
        """Get an extra item or the given default."""
        if self.__pydantic_extra__ is None:
            raise ValueError(f"{type(self)} does not allow extra values.")
        return self.__pydantic_extra__.get(key, default)

    def hash(self) -> str:
        """Hash the object into a hex string."""
        # NOTE: only hashes fields that are not extra
        return tomhash(
            (
                self.__class__.__name__,
                *(
                    (key, _stable_repr(val))
                    for key, val in self.__dict__.items()
                    if key in self.__pydantic_fields__
                ),
            )
        )

    @override
    def __hash__(self) -> int:
        return tomhash_to_int(self.hash())

    @override
    def __eq__(self, other: object) -> bool:
        """Check for equality between self an other, using hashes."""
        return bool(
            isinstance(other, TOMBaseObject)
            and isinstance(other, type(self))
            and self.hash() == other.hash()
        )
