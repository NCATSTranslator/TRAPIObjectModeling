"""Tests for CURIE utility functions in shared.py."""

from translator_tom.models.shared import Curie, biolink, infores


class TestMakeCurie:
    """Tests for Curie() call."""

    def test_call(self) -> None:
        assert Curie("prefix", "reference") == "prefix:reference"


class TestCurieSplit:
    """Tests for Curie.split()."""

    def test_standard_curie(self) -> None:
        assert Curie.split("UniProtKB:P00738") == ("UniProtKB", "P00738")

    def test_no_colon(self) -> None:
        assert Curie.split("nocolon") == ("", "nocolon")

    def test_empty_string(self) -> None:
        assert Curie.split("") == ("", "")

    def test_multiple_colons(self) -> None:
        assert Curie.split("HGNC:1234:extra") == ("HGNC", "1234:extra")

    def test_colon_only(self) -> None:
        assert Curie.split(":") == ("", "")

    def test_trailing_colon(self) -> None:
        assert Curie.split("prefix:") == ("prefix", "")


class TestCurieGetPrefix:
    """Tests for Curie.get_prefix()."""

    def test_standard(self) -> None:
        assert Curie.get_prefix("NCBIGene:1234") == "NCBIGene"

    def test_no_colon(self) -> None:
        assert Curie.get_prefix("bare") == ""


class TestCurieGetReference:
    """Tests for Curie.get_reference()."""

    def test_standard(self) -> None:
        assert Curie.get_reference("NCBIGene:1234") == "1234"

    def test_no_colon(self) -> None:
        assert Curie.get_reference("bare") == "bare"


class TestInfores:
    """Tests for the infores() helper."""

    def test_bare_reference(self) -> None:
        assert infores("molepro") == "infores:molepro"

    def test_idempotent(self) -> None:
        assert infores("infores:molepro") == "infores:molepro"

    def test_empty(self) -> None:
        assert infores("") == "infores:"


class TestBiolink:
    """Tests for the biolink() helper."""

    def test_bare_reference(self) -> None:
        assert biolink("related_to") == "biolink:related_to"

    def test_idempotent(self) -> None:
        assert biolink("biolink:Gene") == "biolink:Gene"

    def test_empty(self) -> None:
        assert biolink("") == "biolink:"
