from abc import ABC
from typing import Any, ClassVar, Literal, Self, overload, override

import ormsgpack
from pydantic import (
    ConfigDict,
    SerializerFunctionWrapHandler,
    TypeAdapter,
    model_serializer,
)
from pydantic.json_schema import (
    DEFAULT_REF_TEMPLATE,
    GenerateJsonSchema,
    JsonSchemaMode,
)
from stablehash import stablehash

# TODO: serialization doesn't maintain extra (because of course not >.>)
# So we need custom serialization for extra=allowed (goodbye, performance!)


class TOMBaseObject(ABC):
    """A base class handling (de)serialization and providing method requirements."""

    # Pydantic internal fields that we want to use
    # This base class isn't pydantic but all instances will be.
    __pydantic_fields__: dict[str, Any]
    __pydantic_config__: ClassVar[ConfigDict]

    _type_adapter: ClassVar[TypeAdapter[Any]]

    def __init__(self) -> None:
        """Prevent base class from being instantiated."""
        raise TypeError("Can't instantiate TOMBaseObject base class.")

    ###### I/O methods #####

    @classmethod
    def get_type_adapter(cls) -> TypeAdapter[Self]:
        """Get a type adapter for this class."""
        try:
            return cls.__dict__["_type_adapter"]
        except KeyError:
            cls._type_adapter = TypeAdapter(cls)
            return cls._type_adapter

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> Self:
        """Deserialize an instance from a python dictionary representation."""
        return cls.get_type_adapter().validate_python(obj)

    def to_dict(self) -> dict[str, Any]:
        """Serialize an instance to python dictionary representation."""
        try:
            adapter = self.__class__._type_adapter
        except AttributeError:
            adapter = self.get_type_adapter()
        return adapter.dump_python(self, mode="json")

    @classmethod
    def from_json(cls, json: str | bytes) -> Self:
        """Deserialize an instance from JSON."""
        # return cls.from_dict(orjson.loads(json))
        # NOTE: Outperforms orjson for larger objects due to single Rust pass
        return cls.get_type_adapter().validate_json(json)

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
        # NOTE: Outperforms orjson for larger objects due to single Rust pass
        try:
            adapter = self.__class__._type_adapter
        except AttributeError:
            adapter = self.get_type_adapter()
        json = adapter.dump_json(self)
        if as_str:
            return json.decode()
        return json

    @classmethod
    def from_msgpack(cls, msgpack: bytes) -> Self:
        """Deserialize an instance from MessagePack."""
        return cls.get_type_adapter().validate_python(ormsgpack.unpackb(msgpack))

    def to_msgpack(self) -> bytes:
        """Serialize an instance to MessagePack."""
        try:
            adapter = self.__class__._type_adapter
        except AttributeError:
            adapter = self.get_type_adapter()
        return ormsgpack.packb(adapter.dump_python(self, mode="json"))

    ##### Misc. #####

    @classmethod
    def json_schema(
        cls,
        *,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        union_format: Literal["any_of", "primitive_type_array"] = "any_of",
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
        mode: JsonSchemaMode = "validation",
    ) -> dict[str, Any]:
        """Get the json schema for this model."""
        try:
            adapter = cls.__class__._type_adapter
        except AttributeError:
            adapter = cls.get_type_adapter()
        return adapter.json_schema(
            by_alias=by_alias,
            ref_template=ref_template,
            union_format=union_format,
            schema_generator=schema_generator,
            mode=mode,
        )

    def __getitem__(self, key: str) -> Any:
        """Get an extra item, if present."""
        return self.__dict__[key]

    def get(self, key: str, default: Any | None) -> Any:
        """Get an extra item or the given default."""
        return self.__dict__.get(key, default)

    def hash(self) -> str:
        """Hash the object into a hex string."""
        # NOTE: only hashes fields that are not extra
        return stablehash(
            (
                self.__class__.__name__,
                *tuple(
                    (key, val)
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
