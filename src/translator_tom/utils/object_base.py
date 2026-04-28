from typing import Any, ClassVar, Literal, Self, cast, overload, override

import orjson
import ormsgpack
from pydantic import BaseModel, ConfigDict
from pydantic.json_schema import (
    DEFAULT_REF_TEMPLATE,
    GenerateJsonSchema,
    JsonSchemaMode,
)
from stablehash import stablehash


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
        # looks redundant but skips over python-level dict handling
        return ormsgpack.packb(orjson.loads(self.__pydantic_serializer__.to_json(self)))

    ##### Misc. #####

    @classmethod
    def json_schema(
        cls,
        *,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
        mode: JsonSchemaMode = "validation",
    ) -> dict[str, Any]:
        """Get the json schema for this model."""
        return cls.json_schema(
            by_alias=by_alias,
            ref_template=ref_template,
            schema_generator=schema_generator,
            mode=mode,
        )

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
        return stablehash(
            (
                self.__class__.__name__,
                *tuple(
                    (key, _stable_repr(val))
                    for key, val in self.__dict__.items()
                    if key in self.__pydantic_fields__
                ),
            )
        ).hexdigest()

    @override
    def __hash__(self) -> int:
        return int(self.hash(), base=16)

    @override
    def __eq__(self, other: object) -> bool:
        """Check for equality between self an other, using hashes."""
        return bool(
            isinstance(other, TOMBaseObject)
            and isinstance(other, type(self))
            and self.hash() == other.hash()
        )
