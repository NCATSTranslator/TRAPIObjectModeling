from __future__ import annotations

__all__ = ["Biolink"]

import threading
from functools import lru_cache
from importlib.resources import files
from typing import TYPE_CHECKING, TypeVar, cast, final

from typing_extensions import override

from translator_tom.models.shared import CURIE, Curie
from translator_tom.utils.cache import lru_copy_cache
from translator_tom.utils.config import TRAPI_CONFIG

if TYPE_CHECKING:
    import bmt
    from linkml_runtime.linkml_model.meta import Element

_T = TypeVar("_T", bound=str)


def _build_toolkit(version: str) -> bmt.Toolkit:
    """Build a bmt Toolkit for a given biolink version.

    Prefers schema files vendored under `translator_tom/data/biolink/<version>/`,
    which avoids http GitHub fetches and time cost. Falls back to fetching from GitHub
    when the configured version is not vendored.

    Imports of `bmt`/`linkml_runtime` are deferred into this function so that
    `import translator_tom` doesn't spend import + parse time until the
    toolkit is first used. See the lazy `Biolink.toolkit` property and
    `Biolink.eager_init()`.

    To vendor a new version, run `task vendor:biolink` after bumping
    `biolink_version` in the config (preferably, keep only the latest).
    """
    import bmt  # noqa: PLC0415  (deferred: keeps bmt out of `import translator_tom`)
    import yaml  # noqa: PLC0415
    from linkml_runtime.utils.schemaview import SchemaView  # noqa: PLC0415

    data_root = files("translator_tom") / "data" / "biolink" / version
    schema_res = data_root / "biolink-model.yaml"
    pmap_res = data_root / "predicate_mapping.yaml"

    if schema_res.is_file() and pmap_res.is_file():
        # bmt.Toolkit.__init__ only sets `.view` and `.pmap`, and reaches the
        # network for both. Build those two attributes here from local files.
        toolkit = bmt.Toolkit.__new__(bmt.Toolkit)
        # SchemaView resolves the model's relative `imports`, so vendored dir must have
        # all relevant files.
        toolkit.view = SchemaView(str(schema_res))
        toolkit.pmap = yaml.safe_load(pmap_res.read_text())
        return toolkit

    base = (
        f"https://raw.githubusercontent.com/biolink/biolink-model/refs/tags/v{version}"
    )
    return bmt.Toolkit(
        schema=f"{base}/biolink-model.yaml",
        predicate_map=f"{base}/predicate_mapping.yaml",
    )


_TOOLKIT_CACHE: dict[str, bmt.Toolkit] = {}
_TOOLKIT_LOCK = threading.Lock()


def _get_toolkit() -> bmt.Toolkit:
    """Return the toolkit for the configured biolink version, building it once."""
    version = TRAPI_CONFIG.biolink_version
    toolkit = _TOOLKIT_CACHE.get(version)
    if toolkit is None:
        with _TOOLKIT_LOCK:  # Ensure no concurrent first-access duplicate builds
            toolkit = _TOOLKIT_CACHE.get(version)
            if toolkit is None:
                toolkit = _TOOLKIT_CACHE[version] = _build_toolkit(version)
    return toolkit


class _BiolinkMeta(type):
    """Metaclass: enables `Biolink(ref)` prefixing and lazy toolkit access."""

    @override
    def __call__(cls, ref: str) -> str:
        """Return a properly-formed biolink element."""
        return f"biolink:{ref.removeprefix('biolink:')}"

    @property
    def toolkit(cls) -> bmt.Toolkit:
        """The bmt Toolkit, built lazily on first access.

        Lazy build improves import time noticeably for use cases where that matters.
        Use `Biolink.eager_init` to force a build (e.g. in FastAPI lifespan).
        """
        return _get_toolkit()


@final
class Biolink(metaclass=_BiolinkMeta):
    """BioLink Model utility. Use utility methods, or call to make prefixed str.

    Biolink.toolkit provides direct bmt access.
    """

    # Predicate = Annotated[CURIE, Field(pattern=r"^biolink:[a-z][a-z_]*$")]
    Predicate = CURIE
    """CURIE for a Biolink 'predicate' slot, taken from the Biolink slot ('is_a') hierarchy rooted in biolink:related_to (snake_case).
    This predicate defines the Biolink relationship between the subject and
    object nodes of a biolink:Association defining a knowledge graph edge.
    """

    # Entity = Annotated[CURIE, Field(pattern=r"^biolink:[A-Z][a-zA-Z]*$")]
    Entity = CURIE
    """Compact URI (CURIE) for a Biolink class, biolink:NamedThing or a child thereof.
    The CURIE must use the prefix 'biolink:'
    followed by the PascalCase class name.
    """

    # Qualifier = Annotated[CURIE, Field(pattern=r"^biolink:[a-z][a-z_]*$")]
    Qualifier = CURIE
    """CURIE for a Biolink 'qualifier' type id such as subject_aspect_qualifier."""

    @staticmethod
    def eager_init() -> None:
        """Eagerly build the toolkit so parse time happens now, instead of on first use."""
        _get_toolkit()

    # Direct passthroughs to the toolkit, exposed for convenience.
    @staticmethod
    def is_qualifier(name: str) -> bool:
        """Whether the given element name is a qualifier (bmt passthrough)."""
        return Biolink.toolkit.is_qualifier(name)

    @staticmethod
    def is_symmetric(name: str) -> bool:
        """Whether the given predicate is symmetric (bmt passthrough)."""
        return Biolink.toolkit.is_symmetric(name)

    @staticmethod
    def get_element(name: str) -> Element | None:
        """Return the biolink element for a name, or None (bmt passthrough)."""
        return Biolink.toolkit.get_element(name)

    @staticmethod
    def rmprefix(element: str) -> str:
        """Remove the `biolink:` prefix from a given element."""
        return Curie.rmprefix(element, "biolink")

    @staticmethod
    def is_valid_predicate(predicate: Biolink.Predicate) -> bool:
        """Validate that a given predicate is a real biolink predicate, including mixins."""
        try:
            return Biolink.toolkit.is_predicate(predicate) or any(
                Biolink("related_to") in Biolink.get_ancestors(desc)
                for desc in Biolink.get_descendants(predicate)
            )
        # ValueError: unknown/malformed term; AttributeError: non-str input. Infra errors propagate.
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def is_valid_category(category: Biolink.Entity) -> bool:
        """Validate that a given category is a real biolink category, including mixins."""
        try:
            return Biolink.toolkit.is_category(category) or any(
                Biolink("NamedThing") in Biolink.get_ancestors(desc)
                for desc in Biolink.get_descendants(category)
            )
        # ValueError: unknown/malformed term; AttributeError: non-str input. Infra errors propagate.
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def is_valid_association(association: Biolink.Entity) -> bool:
        """Validate that a given association is a real biolink association (at any depth)."""
        try:
            # get_ancestors is reflexive, so the root `Association` and any descendant match.
            return "biolink:Association" in Biolink.get_ancestors(association)
        # AttributeError: non-str input; ValueError: unknown/malformed term. Infra errors propagate.
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def get_ancestors(element_str: str) -> list[str]:
        """Get the ancestors of a given element."""
        return Biolink.toolkit.get_ancestors(element_str, formatted=True)

    @staticmethod
    def get_formatted(element_str: str) -> str | None:
        """Get the formatted form of an element.

        Returns None if the given str is not a valid element.
        """
        element = Biolink.toolkit.get_element(element_str)
        if element is not None:
            from bmt import utils  # noqa: PLC0415

            return utils.format_element(element)

    @staticmethod
    def expand(items: str | set[str]) -> set[str]:
        """Safely expand a set of biolink categories or predicates to their descendants.

        Accepts either with or without biolink prefix, but always outputs with biolink prefix.
        """
        initial = {items} if isinstance(items, str) else items
        expanded = {Biolink(item) for item in initial}  # ensure single biolink prefix
        for item in initial:
            expanded.update(Biolink.toolkit.get_descendants(item, formatted=True))
        return expanded

    @staticmethod
    @lru_copy_cache()
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
    @lru_copy_cache()
    def get_descendants(value: _T) -> list[_T]:
        """Get the descendants for a given biolink concept."""
        return cast(list[_T], Biolink.toolkit.get_descendants(value, formatted=True))

    @staticmethod
    @lru_copy_cache()
    def get_descendant_qualifier_values(
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

    @staticmethod
    @lru_copy_cache()
    def get_permissible_value_descendants(enum_name: str, value: str) -> set[str]:
        """Return a permissible value plus its descendants within the named biolink enum.

        Used for constraint hierarchy expansion (e.g. KnowledgeLevelEnum, AgentTypeEnum).
        Raises KeyError if `enum_name` is not a biolink enum (a programming error). An
        unknown `value` (not a permissible value of the enum) expands to just `{value}`.
        """
        enum_def = next(
            (
                definition
                for name, definition in Biolink.toolkit.view.all_enums().items()
                if name == enum_name
            ),
            None,
        )
        if enum_def is None:
            raise KeyError(f"No such biolink enum: {enum_name!r}")
        if value not in cast(dict[str, object], enum_def.permissible_values or {}):
            return {value}
        return {
            value,
            *Biolink.toolkit.get_permissible_value_descendants(value, enum_name),
        }

    @staticmethod
    @lru_cache
    def get_permissible_values(enum_name: str) -> frozenset[str]:
        """Return all permissible value names of the named biolink enum.

        Raises KeyError if `enum_name` is not a biolink enum (a programming error).
        """
        enum_def = next(
            (
                definition
                for name, definition in Biolink.toolkit.view.all_enums().items()
                if name == enum_name
            ),
            None,
        )
        if enum_def is None:
            raise KeyError(f"No such biolink enum: {enum_name!r}")
        return frozenset(cast(dict[str, object], enum_def.permissible_values or {}))

    @staticmethod
    @lru_cache
    def expand_permissible_values(
        enum_name: str, values: frozenset[str]
    ) -> frozenset[str]:
        """Union of each value's permissible-value descendants within the named enum.

        Cached so constraint checks don't rebuild the expanded set per bound Edge.
        """
        return frozenset(
            descendant
            for value in values
            for descendant in Biolink.get_permissible_value_descendants(
                enum_name, value
            )
        )
