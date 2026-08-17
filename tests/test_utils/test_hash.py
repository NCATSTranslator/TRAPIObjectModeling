"""Tests for translator_tom.utils.hash."""

import pytest

from translator_tom.utils import hash as hash_module
from translator_tom.utils.config import TRAPI_CONFIG, HashRepEnum
from translator_tom.utils.hash import tomhash, tomhash_int, tomhash_to_int


class TestTomhash:
    def test_deterministic(self):
        assert tomhash(("a", 1)) == tomhash(("a", 1))

    def test_distinct_inputs_distinct_hashes(self):
        assert tomhash(("a", 1)) != tomhash(("a", 2))

    def test_handles_nested_structures(self):
        assert tomhash({"k": [1, 2, 3]}) == tomhash({"k": [1, 2, 3]})

    def test_encoded_length_matches_config(self):
        digest = tomhash("anything")
        if TRAPI_CONFIG.hash_representation is HashRepEnum.B64:
            # 15 bytes -> 20 chars in unpadded urlsafe base64
            assert len(digest) == 20
        elif TRAPI_CONFIG.hash_representation is HashRepEnum.B32:
            # 15 bytes -> 24 chars in unpadded base32hex
            assert len(digest) == 24
        elif TRAPI_CONFIG.hash_representation is HashRepEnum.HEX:
            assert len(digest) == TRAPI_CONFIG.hash_bytes * 2


class TestTomhashToInt:
    def test_round_trip_through_int(self):
        digest = tomhash("payload")
        as_int = tomhash_to_int(digest)
        assert isinstance(as_int, int)
        assert as_int >= 0

    def test_int_is_deterministic(self):
        assert tomhash_to_int(tomhash("x")) == tomhash_to_int(tomhash("x"))

    def test_distinct_hashes_distinct_ints(self):
        assert tomhash_to_int(tomhash("x")) != tomhash_to_int(tomhash("y"))


class TestTomhashInt:
    """tomhash_int must equal the base64 round-trip, without the detour."""

    def test_matches_roundtrip(self):
        obj = ("a", 1, ("nested", [1, 2, 3]))
        assert tomhash_int(obj) == tomhash_to_int(tomhash(obj))

    def test_deterministic(self):
        assert tomhash_int(("x", 1)) == tomhash_int(("x", 1))

    def test_distinct_inputs_distinct(self):
        assert tomhash_int(("x", 1)) != tomhash_int(("x", 2))

    def test_matches_roundtrip_across_config(self, restore_config):
        # representation-independent (works on the raw digest) and tracks hash_bytes
        obj = ("payload", 7)
        for rep in HashRepEnum:
            TRAPI_CONFIG.hash_representation = rep
            for nbytes in (8, 15, 20):
                TRAPI_CONFIG.hash_bytes = nbytes
                assert tomhash_int(obj) == tomhash_to_int(tomhash(obj))


@pytest.fixture
def restore_config():
    """Restore TRAPI_CONFIG hash settings after mutating them (global singleton)."""
    orig_bytes = TRAPI_CONFIG.hash_bytes
    orig_rep = TRAPI_CONFIG.hash_representation
    try:
        yield
    finally:
        TRAPI_CONFIG.hash_bytes = orig_bytes
        TRAPI_CONFIG.hash_representation = orig_rep


class TestRuntimeConfigMutation:
    """tomhash must reflect runtime changes to TRAPI_CONFIG (read dynamically)."""

    def test_hash_bytes_changes_length(self, restore_config):
        TRAPI_CONFIG.hash_representation = HashRepEnum.HEX
        TRAPI_CONFIG.hash_bytes = 15
        assert len(tomhash("x")) == 30
        TRAPI_CONFIG.hash_bytes = 20
        assert len(tomhash("x")) == 40

    def test_hash_representation_changes_encoding(self, restore_config):
        TRAPI_CONFIG.hash_bytes = 15
        TRAPI_CONFIG.hash_representation = HashRepEnum.B64
        assert len(tomhash("x")) == 20
        TRAPI_CONFIG.hash_representation = HashRepEnum.B32
        assert len(tomhash("x")) == 24
        TRAPI_CONFIG.hash_representation = HashRepEnum.HEX
        assert len(tomhash("x")) == 30


class TestEncoderDecoderRoundTrip:
    """Exercise every (encoder, decoder) pair, regardless of active config."""

    @pytest.mark.parametrize("rep", list(HashRepEnum))
    def test_round_trip(self, rep: HashRepEnum):
        encode = hash_module._ENCODERS[rep]
        decode = hash_module._DECODERS[rep]
        payload = bytes(range(15))
        assert decode(encode(payload)) == payload
