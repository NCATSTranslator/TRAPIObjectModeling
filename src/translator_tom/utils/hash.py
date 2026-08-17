from __future__ import annotations

__all__ = ["tomhash", "tomhash_int", "tomhash_to_int"]

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
    # re-pad (base64 groups of 4) since _b64e strips it
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _b32d(s: str) -> bytes:
    # re-pad (base32 groups of 8) since _b32e strips it
    return base64.b32hexdecode(s + "=" * (-len(s) % 8))


def _b16d(s: str) -> bytes:
    return bytes.fromhex(s)


_DECODERS: dict[HashRepEnum, Callable[[str], bytes]] = {
    HashRepEnum.HEX: _b16d,
    HashRepEnum.B32: _b32d,
    HashRepEnum.B64: _b64d,
}


def tomhash(obj: object) -> str:
    """Hash an object via stablehash and encode per TRAPI_CONFIG.hash_representation.

    Significantly slower than built-in hash, especially if given arbitrary objects.
    Use sparingly, only where a stable hash is actually needed, or where the hashing scope
    can be minimized.
    """
    # read config dynamically so runtime changes take effect
    return _ENCODERS[TRAPI_CONFIG.hash_representation](
        stablehash(obj).digest()[: TRAPI_CONFIG.hash_bytes]
    )


def tomhash_to_int(tom_hash: str) -> int:
    """Convert a tomhash to int."""
    return int.from_bytes(
        _DECODERS[TRAPI_CONFIG.hash_representation](tom_hash), byteorder="big"
    )


def tomhash_int(obj: object) -> int:
    """Hash an object directly to int, skipping the base64 encode/decode detour.

    Yields the same value as tomhash_to_int(tomhash(obj)) without the round-trip.
    """
    # read config dynamically so runtime changes take effect
    return int.from_bytes(
        stablehash(obj).digest()[: TRAPI_CONFIG.hash_bytes], byteorder="big"
    )
