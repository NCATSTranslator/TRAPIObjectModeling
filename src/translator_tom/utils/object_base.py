from abc import ABC
from typing import Any, ClassVar, Literal, Self, overload, override

import ormsgpack
from pydantic import TypeAdapter
from stablehash import stablehash


class TOMBaseObject(ABC):
    """A base class handling (de)serialization and providing method requirements."""

    _type_adapter: ClassVar[TypeAdapter[Any]]

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
        return adapter.dump_python(self)

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

    def hash(self) -> str:
        """Hash the object into a hex string."""
        return stablehash(
            (
                self.__class__.__name__,
                *self.__dict__.items(),
                # TODO: Decide if extra should factor into hash?
                # *getattr(self, "__pydantic_extra__", {}).items(),
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
