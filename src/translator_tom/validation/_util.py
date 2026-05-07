from __future__ import annotations

from collections.abc import Collection, Iterable
from functools import singledispatch
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import AnyUrl, TypeAdapter, ValidationError

from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBase

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
    obj: TOMBase,
    location: Location | None = None,
    **kwargs: Any,
) -> SemanticValidationResult:
    """Validate a TOM object semantically.

    Returns a tuple of warnings and errors.
    An empty errors list means validation passed.

    Context can be provided via keyword arguments. When called without context, validates only what can be checked standalone.
    """
    return always_valid()


def validate_many(
    *obj: TOMBase, locations: list[Location] | None = None, **kwargs: Any
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
    obj: TOMBase | None,
    location: Location | None = None,
    **kwargs: Any,
) -> SemanticValidationResult:
    """Validate the value if it's not None, or return valid otherwise."""
    if obj is None:
        return SemanticValidationWarningList(), SemanticValidationErrorList()
    return semantic_validate(obj, location, **kwargs)


def passes_semantic_validation(obj: TOMBase, **kwargs: Any) -> bool:
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


def validate_biolink_element(
    element: str,
    element_type: Literal["category", "predicate", "association"],
    location: Location | None = None,
) -> SemanticValidationResult:
    """Validate a given element."""
    warnings, errors = SemanticValidationWarningList(), SemanticValidationErrorList()

    element_valid = {
        "category": Biolink.is_valid_category,
        "predicate": Biolink.is_valid_predicate,
        "association": Biolink.is_valid_association,
    }[element_type](element)

    if not element_valid:
        errors.append(
            SemanticValidationError(
                f"{element_type.title()} `{element}` is not a valid BioLink {element_type}.",
                location,
            )
        )
        return warnings, errors

    if element != Biolink.get_formatted(element):
        errors.append(
            SemanticValidationError(
                f"{element_type.title()} `{element}` is not in a valid format for use.",
                location,
            )
        )
        return warnings, errors

    bmt_element = Biolink.get_element(element)
    if bmt_element is None:
        raise ValueError(f"Valid {element_type} `{element}` is not a valid element?")

    if bmt_element.deprecated:
        warning_msg = f"{element_type.title()} `{element}` is deprecated."
        if bmt_element.deprecated_element_has_exact_replacement is not None:
            warning_msg += f" Use replacement instead: `{Biolink.get_formatted(bmt_element.deprecated_element_has_exact_replacement)}`."
        elif bmt_element.deprecated_element_has_possible_replacement:
            warning_msg += f" Possible replacement: `{Biolink.get_formatted(bmt_element.deprecated_element_has_possible_replacement)}`."

        warnings.append(SemanticValidationWarning(warning_msg, location))

    return warnings, errors


def validate_predicate(
    predicate: Biolink.Predicate, location: Location | None = None
) -> SemanticValidationResult:
    """Validate that a given predicate is a real biolink predicate."""
    return validate_biolink_element(predicate, "predicate", location)


def validate_category(
    category: Biolink.Entity, location: Location | None = None
) -> SemanticValidationResult:
    """Validate that a given category is a real biolink category."""
    return validate_biolink_element(category, "category", location)


def validate_association(
    association: Biolink.Entity, location: Location | None = None
) -> SemanticValidationResult:
    """Validate that a given association is a real biolink association."""
    return validate_biolink_element(association, "association", location)


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
