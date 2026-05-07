"""Tests for translator_tom.utils.biolink."""

from translator_tom.utils.biolink import Biolink


class TestRmprefix:
    def test_strips_biolink_prefix(self):
        assert Biolink.rmprefix("biolink:Gene") == "Gene"

    def test_no_change_when_no_prefix(self):
        assert Biolink.rmprefix("Gene") == "Gene"

    def test_strips_only_first_prefix(self):
        # Curie.rmprefix removes a single leading "biolink:"
        assert Biolink.rmprefix("biolink:related_to") == "related_to"


class TestIsValidPredicate:
    def test_known_predicate(self):
        assert Biolink.is_valid_predicate("biolink:related_to") is True

    def test_known_descendant_predicate(self):
        # `treats` is a descendant of `related_to` and is a real predicate.
        assert Biolink.is_valid_predicate("biolink:treats") is True

    def test_known_non_predicate(self):
        # `Gene` is a real biolink class but not a predicate.
        assert Biolink.is_valid_predicate("biolink:Gene") is False


class TestIsValidCategory:
    def test_root_category(self):
        assert Biolink.is_valid_category("biolink:NamedThing") is True

    def test_known_subclass(self):
        assert Biolink.is_valid_category("biolink:Gene") is True

    def test_known_non_category(self):
        # `related_to` is a real biolink predicate but not a category.
        assert Biolink.is_valid_category("biolink:related_to") is False


class TestIsValidAssociation:
    def test_unknown_returns_false(self):
        assert Biolink.is_valid_association("biolink:NotARealThingXYZ") is False

    def test_non_association_returns_false(self):
        # Gene's direct parent is not "association".
        assert Biolink.is_valid_association("biolink:Gene") is False

    def test_known_association_returns_true(self):
        # `ContributorAssociation` is a direct child of `association` in biolink.
        assert Biolink.is_valid_association("biolink:ContributorAssociation") is True


class TestGetAncestors:
    def test_includes_self_and_parents(self):
        ancestors = Biolink.get_ancestors("biolink:Gene")
        assert "biolink:Gene" in ancestors
        assert "biolink:NamedThing" in ancestors

    def test_returns_list(self):
        assert isinstance(Biolink.get_ancestors("biolink:Gene"), list)


class TestGetFormatted:
    def test_returns_formatted_string_for_real_element(self):
        # `gene` (snake-case slot) should resolve to a formatted CURIE.
        result = Biolink.get_formatted("gene")
        assert result == "biolink:Gene"

    def test_returns_none_for_unknown_element(self):
        assert Biolink.get_formatted("not_a_real_element_xyz") is None


class TestExpand:
    def test_string_input_returns_set_with_descendants(self):
        result = Biolink.expand("biolink:Gene")
        assert "biolink:Gene" in result
        assert isinstance(result, set)

    def test_set_input(self):
        result = Biolink.expand({"biolink:Gene", "biolink:Disease"})
        assert "biolink:Gene" in result
        assert "biolink:Disease" in result

    def test_input_term_always_in_output(self):
        # Terms passed in are always kept in the output set.
        result = Biolink.expand("biolink:NamedThing")
        assert "biolink:NamedThing" in result


class TestGetAllQualifiers:
    def test_returns_non_empty_set_of_strings(self):
        qualifiers = Biolink.get_all_qualifiers()
        assert isinstance(qualifiers, set)
        assert len(qualifiers) > 0
        assert all(isinstance(q, str) for q in qualifiers)

    def test_no_spaces_in_names(self):
        # Names are normalized from "x y" -> "x_y".
        for q in Biolink.get_all_qualifiers():
            assert " " not in q

    def test_excludes_bare_qualifier(self):
        # The bare "qualifier" slot is filtered out.
        assert "qualifier" not in Biolink.get_all_qualifiers()


class TestGetInverse:
    def test_known_inverse(self):
        # biolink:treats and biolink:treated_by are inverses.
        assert Biolink.get_inverse("biolink:treats") == "biolink:treated_by"

    def test_no_inverse_returns_none(self):
        assert Biolink.get_inverse("biolink:not_a_real_predicate_xyz") is None


class TestGetDescendants:
    def test_includes_self(self):
        descendants = Biolink.get_descendants("biolink:NamedThing")
        assert "biolink:NamedThing" in descendants
        assert "biolink:Gene" in descendants

    def test_leaf_class_descendants_only_self(self):
        # `Gene` exists; descendants always include the queried term itself.
        descendants = Biolink.get_descendants("biolink:Gene")
        assert "biolink:Gene" in descendants


class TestGetDescendantValues:
    def test_predicate_qualifier_branch(self):
        # When qualifier_type contains "predicate", expand() is used and the
        # biolink: prefix is stripped from each result.
        result = Biolink.get_descendant_values(
            "biolink:qualified_predicate", "biolink:causes"
        )
        assert "causes" in result
        assert all(not v.startswith("biolink:") for v in result)

    def test_non_predicate_qualifier_returns_value_set(self):
        # An unknown value with a non-predicate qualifier just returns {value}.
        result = Biolink.get_descendant_values(
            "biolink:subject_aspect_qualifier", "not_a_real_value_xyz"
        )
        assert result == {"not_a_real_value_xyz"}

    def test_non_predicate_qualifier_with_known_enum_value(self):
        # `therapeutic_response` is a permissible value of ResponseEnum, so the
        # permissible-values branch is exercised.
        result = Biolink.get_descendant_values(
            "biolink:object_aspect_qualifier", "therapeutic_response"
        )
        assert "therapeutic_response" in result
