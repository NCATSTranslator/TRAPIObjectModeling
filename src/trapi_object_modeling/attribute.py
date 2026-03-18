from __future__ import annotations

from typing import Any, override

from pydantic import ConfigDict, JsonValue, SkipValidation
from pydantic.dataclasses import dataclass

from trapi_object_modeling.shared import CURIE
from trapi_object_modeling.utils.object_base import (
    Location,
    SemanticValidationErrorList,
    SemanticValidationResult,
    SemanticValidationWarningList,
    TOMBaseObject,
)
from trapi_object_modeling.utils.semantic_validation import (
    extend_location,
    get_list_locations,
    validate_many,
    validate_url,
    validation_pipeline,
)


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class Attribute(TOMBaseObject):
    """Generic attribute for a node or an edge that expands the key-value pair concept by including fields for additional metadata.

    These fields can be used to describe the source of the statement made in a key-value
    pair of the attribute object, or describe the attribute's value itself
    including its semantic type, or a url providing additional information
    about it. An attribute may be further qualified with sub-attributes
    (for example to provide confidence intervals on a value).
    """

    attribute_type_id: CURIE
    """The 'key' of the attribute object, holding a CURIE of an ontology property defining the attribute (preferably the CURIE of a Biolink association slot).

    This property captures the relationship asserted to hold between the value of the attribute, and the node
    or edge from  which it hangs. For example, that a value of
    '0.000153' represents a p-value supporting an edge, or that
    a value of 'ChEMBL' represents the original source of the knowledge
    expressed in the edge.
    """

    original_attribute_name: str | None = None
    """The term used by the original source of an attribute to describe the meaning or significance of the value it captures.

    This may be a column name in a source tsv file, or a key in a source json
    document for the field in the data that held the attribute's
    value. Capturing this information  where possible lets us preserve
    what the original source said. Note that the data type is string'
    but the contents of the field could also be a CURIE of a third
    party ontology term.
    """

    # JSON value inherently doesn't need validation if you're validating from JSON
    value: SkipValidation[JsonValue]
    """Value of the attribute. May be any data type, including a list."""

    value_type_id: CURIE | None = None
    """CURIE describing the semantic type of an  attribute's value.

    Use a Biolink class if possible, otherwise a term from an external
    ontology. If a suitable CURIE/identifier does not exist, enter a
    descriptive phrase here and submit the new type for consideration
    by the appropriate authority.
    """

    attribute_source: str | None = None
    """The source of the core assertion made by the key-value pair of an attribute object.

    Use a CURIE or namespace designator for this resource where possible.
    """

    value_url: str | None = None
    """Human-consumable URL linking to a web document that provides additional information about an attribute's value (not the node or the edge fom which it hangs)."""

    description: str | None = None
    """Human-readable description for the attribute and its value."""

    attributes: list[Attribute] | None = None
    """A list of attributes providing further information about the parent attribute (for example to provide provenance information about the parent attribute)."""

    @property
    def attributes_list(self) -> list[Attribute]:
        """Get the attributes as a guaranteed list, even if they are represented as None."""
        return self.attributes if self.attributes is not None else []

    @override
    def semantic_validate(
        self,
        location: Location | None = None,
        **kwargs: Any,
    ) -> SemanticValidationResult:
        warnings, errors = (
            SemanticValidationWarningList(),
            SemanticValidationErrorList(),
        )

        if self.value_url is not None:
            _, new_err = validate_url(
                self.value_url, extend_location(location, "value_url")
            )
            errors.extend(new_err)

        return validation_pipeline(
            (warnings, errors),
            validate_many(
                *self.attributes_list,
                locations=get_list_locations(
                    self.attributes_list, extend_location(location, "attributes")
                ),
            ),
        )
