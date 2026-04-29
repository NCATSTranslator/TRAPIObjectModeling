from __future__ import annotations

from functools import lru_cache
from typing import Annotated, ClassVar, TypeVar, cast, final, override

import bmt
from bmt import utils
from pydantic import Field

from translator_tom.models.shared import CURIE, Curie
from translator_tom.utils.config import TRAPI_CONFIG

_T = TypeVar("_T", bound=str)


class _BiolinkMeta(type):
    """Metaclass that allows Biolink to be called for prefix construction."""

    @override
    def __call__(cls, ref: str) -> str:
        """Return a properly-formed biolink element."""
        return f"biolink:{ref.removeprefix('biolink:')}"


@final
class Biolink(metaclass=_BiolinkMeta):
    """BioLink Model utility. Use utility methods, or call to make prefixed str.

    Biolink.toolkit provides direct bmt access.
    """

    Predicate = Annotated[CURIE, Field(pattern=r"^biolink:[a-z][a-z_]*$")]
    """CURIE for a Biolink 'predicate' slot, taken from the Biolink slot ('is_a') hierarchy rooted in biolink:related_to (snake_case).
    This predicate defines the Biolink relationship between the subject and
    object nodes of a biolink:Association defining a knowledge graph edge.
    """

    Entity = Annotated[CURIE, Field(pattern=r"^biolink:[A-Z][a-zA-Z]*$")]
    """Compact URI (CURIE) for a Biolink class, biolink:NamedThing or a child thereof.
    The CURIE must use the prefix 'biolink:'
    followed by the PascalCase class name.
    """

    Qualifier = Annotated[CURIE, Field(pattern=r"^biolink:[a-z][a-z_]*$")]
    """CURIE for a Biolink 'qualifier' type id such as subject_aspect_qualifier."""

    toolkit: ClassVar[bmt.Toolkit] = bmt.Toolkit(
        schema=f"https://raw.githubusercontent.com/biolink/biolink-model/refs/tags/v{TRAPI_CONFIG.biolink_version}/biolink-model.yaml",
        predicate_map=f"https://raw.githubusercontent.com/biolink/biolink-model/refs/tags/v{TRAPI_CONFIG.biolink_version}/predicate_mapping.yaml",
    )

    # Direct passthroughs to the toolkit, exposed for convenience.
    is_qualifier = staticmethod(toolkit.is_qualifier)
    is_symmetric = staticmethod(toolkit.is_symmetric)
    is_predicate = staticmethod(toolkit.is_predicate)
    is_category = staticmethod(toolkit.is_category)
    get_element = staticmethod(toolkit.get_element)
    get_ancestors = staticmethod(toolkit.get_ancestors)

    @staticmethod
    def get_formatted(element_str: str) -> str | None:
        """Get the formatted form of an element.

        Returns None if the given str is not a valid element.
        """
        element = Biolink.toolkit.get_element(element_str)
        if element is not None:
            return utils.format_element(element)

    @staticmethod
    def expand(items: str | set[str]) -> set[str]:
        """Safely expand a set of biolink categories or predicates to their descendants.

        Accepts either with or without biolink prefix, but always outputs with biolink prefix.
        """
        initial = {items} if isinstance(items, str) else items
        expanded = set(initial)
        for item in initial:
            expanded.update(Biolink.toolkit.get_descendants(item, formatted=True))
        return expanded

    @staticmethod
    @lru_cache
    def get_all_qualifiers() -> set[Biolink.Qualifier]:
        """Return all qualifiers in the biolink model."""
        slots = Biolink.toolkit.get_all_edge_properties()
        return {
            slot.replace(" ", "_")
            for slot in slots
            if Biolink.toolkit.is_qualifier(slot) and slot != "qualifier"
        }

    @staticmethod
    def get_inverse(predicate: Biolink.Predicate) -> Biolink.Predicate | None:
        """Return the inverse of a given predicate."""
        return Biolink.toolkit.get_inverse_predicate(predicate, formatted=True)

    @staticmethod
    def get_descendants(value: _T) -> list[_T]:
        """Get the descendants for a given biolink concept."""
        return cast(list[_T], Biolink.toolkit.get_descendants(value, formatted=True))

    @staticmethod
    @lru_cache
    def get_descendant_values(
        qualifier_type: Biolink.Qualifier, value: str
    ) -> set[str]:
        """Given a biolink qualifier and associated value, return applicable descendant values."""
        if "predicate" in qualifier_type:
            return {Curie.rmprefix(predicate) for predicate in Biolink.expand(value)}

        permissible_values: set[str] = {value}
        for enum_name, enum_def in Biolink.toolkit.view.all_enums().items():
            if value in cast(dict[str, object], enum_def.permissible_values or {}):
                permissible_values.update(
                    Biolink.toolkit.get_permissible_value_descendants(value, enum_name)
                )

        return permissible_values
