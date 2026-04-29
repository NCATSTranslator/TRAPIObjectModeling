from __future__ import annotations

from collections.abc import Collection, Iterable
from functools import singledispatch
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import AnyUrl, TypeAdapter, ValidationError

from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBaseObject

url_adapter = TypeAdapter(AnyUrl)

Location = tuple[str | int, ...]
"""A tuple of keys/indicies that can be used to find a specific value in nested JSON."""


class SemanticValidationError(Exception):
    """An error that represents a Semantic Validation failure."""

    message: str
    location: Location

    def __init__(
        self, message: str, location: Location | None = None, *args: object
    ) -> None:
        """Initialize an instance."""
        super().__init__(message, *args)
        self.message = message
        self.location = location if location is not None else ()


class SemanticValidationWarning(Warning):
    """An warning that is of concern, but doesn't fail semantic validation."""

    message: str
    location: Location

    def __init__(
        self, message: str, location: Location | None = None, *args: object
    ) -> None:
        """Initialize an instance."""
        super().__init__(message, *args)
        self.message = message
        self.location = location if location is not None else ()


SemanticValidationErrorList = list[SemanticValidationError]
SemanticValidationWarningList = list[SemanticValidationWarning]

SemanticValidationResult = tuple[
    SemanticValidationWarningList, SemanticValidationErrorList
]


@runtime_checkable
class GraphWithNodes(Protocol):
    """A protocol for any graph object with a simple nodes dict."""

    nodes: dict[Any, Any]


@runtime_checkable
class GraphWithEdges(Protocol):
    """A protocol for any graph object with an edges dict."""

    edges: dict[Any, Any]


class SubjectObjectMapping(Protocol):
    """A protocol for any edge-like mapping between a subject and an object."""

    subject: str
    object: str


@singledispatch
def semantic_validate(
    obj: TOMBaseObject,  # pyright:ignore[reportUnusedParameter]
    location: Location | None = None,  # pyright:ignore[reportUnusedParameter]
    **kwargs: Any,  # pyright:ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    """Validate a TOM object semantically.

    Returns a tuple of warnings and errors.
    An empty errors list means validation passed.

    Context can be provided via keyword arguments. When called without context, validates only what can be checked standalone.
    """
    return always_valid()


def validate_many(
    *obj: TOMBaseObject, locations: list[Location] | None = None, **kwargs: Any
) -> SemanticValidationResult:
    """Validate every TOMBaseObject item, returning their combined feedback."""
    warnings, errors = (
        SemanticValidationWarningList(),
        SemanticValidationErrorList(),
    )
    for i, to_validate in enumerate(obj):
        location = locations[i] if locations is not None else None
        new_warn, new_err = semantic_validate(to_validate, location=location, **kwargs)
        warnings.extend(new_warn)
        errors.extend(new_err)

    return warnings, errors


def valid_if_missing(
    obj: TOMBaseObject | None,
    location: Location | None = None,
    **kwargs: Any,
) -> SemanticValidationResult:
    """Validate the value if it's not None, or return valid otherwise."""
    if obj is None:
        return SemanticValidationWarningList(), SemanticValidationErrorList()
    return semantic_validate(obj, location, **kwargs)


def passes_semantic_validation(obj: TOMBaseObject, **kwargs: Any) -> bool:
    """Check if an instance passes semantic validation, discarding messages."""
    _, errors = semantic_validate(obj, **kwargs)
    return len(errors) == 0


def extend_location(
    location: Location | None, new_end: str | int, *additional: str | int
) -> Location:
    """Extend a location, or start a new one if given None."""
    return (*(location or ()), new_end, *additional)


def validation_pipeline(
    result: SemanticValidationResult, *results: SemanticValidationResult
) -> SemanticValidationResult:
    """Validate multiple steps and combine their outputs."""
    warnings, errors = result

    for new_warn, new_err in results:
        warnings.extend(new_warn)
        errors.extend(new_err)

    return warnings, errors


def validate_url(
    url: str, location: Location | None = None
) -> SemanticValidationResult:
    """Validate a URL against Pydantic's least strict URL requirements."""
    try:
        url_adapter.validate_python(url)
        return SemanticValidationWarningList(), SemanticValidationErrorList()
    except ValidationError as e:
        return SemanticValidationWarningList(), SemanticValidationErrorList(
            [
                SemanticValidationError(err["msg"], location=location)
                for err in e.errors()
            ]
        )


def validate_predicate(
    predicate: Biolink.Predicate, location: Location | None = None
) -> SemanticValidationResult:
    """Validate that a given predicate is a real biolink predicate."""
    warnings, errors = SemanticValidationWarningList(), SemanticValidationErrorList()

    if not Biolink.is_predicate(predicate):
        errors.append(
            SemanticValidationError(
                f"Predicate `{predicate}` is not a valid BioLink predicate.", location
            )
        )
        return warnings, errors

    if predicate != Biolink.get_formatted(predicate):
        errors.append(
            SemanticValidationError(
                f"Predicate `{predicate}` is not in a valid format for use.", location
            )
        )
        return warnings, errors

    element = Biolink.get_element(predicate)
    if element is None:
        raise ValueError("Valid predicate `{predicate}` is not a valid element?")

    if element.deprecated:
        warning_msg = f"Predicate `{predicate}` is deprecated."
        if element.deprecated_element_has_exact_replacement is not None:
            warning_msg += f" Use replacement instead: `{Biolink.get_formatted(element.deprecated_element_has_exact_replacement)}`."
        elif element.deprecated_element_has_possible_replacement:
            warning_msg += f" Possible replacement: `{Biolink.get_formatted(element.deprecated_element_has_possible_replacement)}`."

        warnings.append(SemanticValidationWarning(warning_msg, location))

    return warnings, errors


def validate_category(
    category: Biolink.Entity, location: Location | None = None
) -> SemanticValidationResult:
    """Validate that a given predicate is a real biolink predicate."""
    warnings, errors = SemanticValidationWarningList(), SemanticValidationErrorList()

    try:
        valid_category = not Biolink.is_category(category) or any(
            "biolink:NamedThing" in Biolink.get_ancestors(desc, formatted=True)
            for desc in Biolink.get_descendants(category)
        )
    except Exception:
        valid_category = False

    if not valid_category:
        errors.append(
            SemanticValidationError(
                f"Category `{category}` is not a valid BioLink category.", location
            )
        )
        return warnings, errors

    if category != Biolink.get_formatted(category):
        errors.append(
            SemanticValidationError(
                f"Category `{category}` is not in a valid format for use.", location
            )
        )
        return warnings, errors

    element = Biolink.get_element(category)
    if element is None:
        raise ValueError("Valid category `{category}` is not a valid element?")

    if element.deprecated:
        warning_msg = f"Category `{category}` is deprecated."
        if element.deprecated_element_has_exact_replacement is not None:
            warning_msg += f" Use replacement instead: `{Biolink.get_formatted(element.deprecated_element_has_exact_replacement)}`."
        elif element.deprecated_element_has_possible_replacement:
            warning_msg += f" Possible replacement: `{Biolink.get_formatted(element.deprecated_element_has_possible_replacement)}`."

        warnings.append(SemanticValidationWarning(warning_msg, location))

    return warnings, errors


def validate_association(
    association: Biolink.Entity, location: Location | None = None
) -> SemanticValidationResult:
    """Validate that a given association is a real biolink association."""
    warnings, errors = SemanticValidationWarningList(), SemanticValidationErrorList()

    element = Biolink.get_element(association)
    if element is None or element.is_a == "association":
        errors.append(
            SemanticValidationError(
                f"Association `{association}` is not a valid BioLink association.",
                location,
            )
        )
        return warnings, errors

    if association != Biolink.get_formatted(association):
        errors.append(
            SemanticValidationError(
                f"Association `{association}` is not in a valid format for use.",
                location,
            )
        )
        return warnings, errors

    if element.deprecated:
        warning_msg = f"Association `{association}` is deprecated."
        if element.deprecated_element_has_exact_replacement is not None:
            warning_msg += f" Use replacement instead: `{Biolink.get_formatted(element.deprecated_element_has_exact_replacement)}`."
        elif element.deprecated_element_has_possible_replacement:
            warning_msg += f" Possible replacement: `{Biolink.get_formatted(element.deprecated_element_has_possible_replacement)}`."

        warnings.append(SemanticValidationWarning(warning_msg, location))

    return warnings, errors


def always_valid() -> SemanticValidationResult:
    """Return empty lists because there is either no way for the object to be inavlid, or no way to check."""
    return SemanticValidationWarningList(), SemanticValidationErrorList()


def get_list_locations(
    objs: list[Any], location: Location | None = None
) -> list[Location]:
    """Get the Locations for each item the list."""
    locations = [Location((i,)) for i in range(len(objs))]
    if location is not None:
        locations = [Location((*location, *loc)) for loc in locations]

    return locations


def get_dict_locations(
    dictionary: dict[str, Any], location: Location | None = None
) -> list[Location]:
    """Get the Locations for each item in the dict."""
    locations = [Location((key,)) for key in dictionary]
    if location is not None:
        locations = [Location((*location, *loc)) for loc in locations]

    return locations


def validate_keys_exist(
    keys: Iterable[Any],
    host: Collection[Any],
    key_label: str,
    mapping_label: str,
    location: Location | None = None,
) -> SemanticValidationResult:
    """Check that every key is present in the mapping."""
    warnings, errors = (
        SemanticValidationWarningList(),
        SemanticValidationErrorList(),
    )
    for key in keys:
        if key not in host:
            errors.append(
                SemanticValidationError(
                    f"{key_label} {key} is not present in {mapping_label}.",
                    location or (),
                )
            )
    return warnings, errors


def validate_node_exists(
    self: SubjectObjectMapping,
    end: Literal["subject", "object"],
    graph: GraphWithNodes,
    graph_name: str,
    location: Location | None,
) -> SemanticValidationResult:
    """Validate that the given nodes exists in the graph."""
    warnings, errors = (
        SemanticValidationWarningList(),
        SemanticValidationErrorList(),
    )

    node = self.subject if end == "subject" else self.object

    if self.subject not in graph.nodes:
        errors.append(
            SemanticValidationError(
                f"{end.capitalize()} `{node}` is not present in {graph_name}.",
                extend_location(location, end),
            )
        )

    return warnings, errors
