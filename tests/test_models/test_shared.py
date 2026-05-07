"""Tests for translator_tom.models.shared."""

from typing import Any

import pytest

from translator_tom.models.shared import (
    Curie,
    FastJsonValue,
    KnowledgeTypeEnum,
    infores,
)
from translator_tom.utils.object_base import TOMBase


class TestMakeCurie:
    def test_call(self):
        assert Curie("prefix", "reference") == "prefix:reference"

    def test_empty_reference(self):
        assert Curie("prefix", "") == "prefix:"

    def test_empty_prefix(self):
        assert Curie("", "reference") == ":reference"


class TestCurieSplit:
    def test_standard_curie(self):
        assert Curie.split("UniProtKB:P00738") == ("UniProtKB", "P00738")

    def test_no_colon(self):
        assert Curie.split("nocolon") == ("", "nocolon")

    def test_empty_string(self):
        assert Curie.split("") == ("", "")

    def test_multiple_colons(self):
        assert Curie.split("HGNC:1234:extra") == ("HGNC", "1234:extra")

    def test_colon_only(self):
        assert Curie.split(":") == ("", "")

    def test_trailing_colon(self):
        assert Curie.split("prefix:") == ("prefix", "")


class TestCurieGetPrefix:
    def test_standard(self):
        assert Curie.get_prefix("NCBIGene:1234") == "NCBIGene"

    def test_no_colon(self):
        assert Curie.get_prefix("bare") == ""


class TestCurieGetReference:
    def test_standard(self):
        assert Curie.get_reference("NCBIGene:1234") == "1234"

    def test_no_colon(self):
        assert Curie.get_reference("bare") == "bare"

    def test_with_explicit_prefix_no_colon(self):
        assert Curie.get_reference("NCBIGene:1234", prefix="NCBIGene") == "1234"

    def test_with_explicit_prefix_trailing_colon(self):
        assert Curie.get_reference("NCBIGene:1234", prefix="NCBIGene:") == "1234"

    def test_explicit_prefix_does_not_match(self):
        # If the supplied prefix isn't actually present, removeprefix is a no-op.
        assert (
            Curie.get_reference("NCBIGene:1234", prefix="HGNC")
            == "NCBIGene:1234"
        )


class TestCurieEnsurePrefix:
    def test_replaces_existing_prefix(self):
        assert Curie.ensure_prefix("HGNC", "NCBIGene:1234") == "HGNC:1234"

    def test_adds_prefix_when_missing(self):
        # `bare` has no colon; get_reference returns it unchanged.
        assert Curie.ensure_prefix("HGNC", "bare") == "HGNC:bare"


class TestCurieAliases:
    def test_rmprefix_is_get_reference(self):
        assert Curie.rmprefix("NCBIGene:1234") == "1234"
        assert Curie.rmprefix("NCBIGene:1234", prefix="NCBIGene") == "1234"

    def test_rmref_is_get_prefix(self):
        assert Curie.rmref("NCBIGene:1234") == "NCBIGene"
        assert Curie.rmref("bare") == ""


class TestInfores:
    def test_bare_reference(self):
        assert infores("molepro") == "infores:molepro"

    def test_idempotent(self):
        assert infores("infores:molepro") == "infores:molepro"

    def test_empty(self):
        assert infores("") == "infores:"


class TestKnowledgeTypeEnum:
    def test_lookup_value(self):
        assert KnowledgeTypeEnum.lookup.value == "lookup"

    def test_inferred_value(self):
        assert KnowledgeTypeEnum.inferred.value == "inferred"

    def test_string_subclass(self):
        # Declared as `(str, Enum)` so members compare equal to plain strings.
        assert KnowledgeTypeEnum.lookup == "lookup"
        assert KnowledgeTypeEnum.inferred == "inferred"


class _FastJsonValueModel(TOMBase):
    """Minimal TOMBase used to exercise FastJsonValue validate/dump."""

    payload: FastJsonValue


class TestFastJsonValue:
    @pytest.mark.parametrize(
        "value",
        [
            True,
            42,
            3.14,
            "string",
            [1, 2, 3],
            {"key": "value", "nested": [1, {"k": True}]},
        ],
    )
    def test_round_trips_json_compatible_value(self, value: Any):
        m = _FastJsonValueModel(payload=value)
        assert m.payload == value
        assert m.to_dict() == {"payload": value}

    def test_none_payload_dropped_on_serialization(self):
        # TOMBase.to_dict uses exclude_none=True, so a None payload is omitted
        # from the dict — even though the field is required.
        m = _FastJsonValueModel(payload=None)
        assert m.payload is None
        assert m.to_dict() == {}

    def test_round_trip_through_json(self):
        m = _FastJsonValueModel(payload={"k": [1, 2, 3]})
        restored = _FastJsonValueModel.from_json(m.to_json())
        assert restored.payload == {"k": [1, 2, 3]}

    def test_passes_through_arbitrary_python_object(self):
        # any_schema skips validation, so non-JSON values like sets are stored
        # unchanged at the python level.
        m = _FastJsonValueModel.model_construct(payload={1, 2, 3})
        assert m.payload == {1, 2, 3}
