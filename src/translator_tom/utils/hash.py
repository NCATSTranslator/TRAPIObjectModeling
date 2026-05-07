from __future__ import annotations

__all__ = ["tomhash", "tomhash_to_int"]

import base64
from collections.abc import Callable

from stablehash import stablehash

from translator_tom.utils.config import TRAPI_CONFIG, HashRepEnum


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _b32e(b: bytes) -> str:
    return base64.b32hexencode(b).rstrip(b"=").decode("ascii")


_ENCODERS: dict[HashRepEnum, Callable[[bytes], str]] = {
    HashRepEnum.HEX: bytes.hex,
    HashRepEnum.B32: _b32e,
    HashRepEnum.B64: _b64e,
}


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s)


def _b32d(s: str) -> bytes:
    return base64.b32hexdecode(s)


def _b16d(s: str) -> bytes:
    return bytes.fromhex(s)


_DECODERS: dict[HashRepEnum, Callable[[str], bytes]] = {
    HashRepEnum.HEX: _b16d,
    HashRepEnum.B32: _b32d,
    HashRepEnum.B64: _b64d,
}

_HASH_BYTES = TRAPI_CONFIG.hash_bytes
_ENCODE = _ENCODERS[TRAPI_CONFIG.hash_representation]
_DECODE = _DECODERS[TRAPI_CONFIG.hash_representation]


def tomhash(obj: object) -> str:
    """Hash an object via stablehash and encode per TRAPI_CONFIG.hash_representation."""
    return _ENCODE(stablehash(obj).digest()[:_HASH_BYTES])


def tomhash_to_int(tom_hash: str) -> int:
    """Convert a tomhash to int."""
    return int.from_bytes(_DECODE(tom_hash), byteorder="big")
