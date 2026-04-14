from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.shared import AuxGraphID

if TYPE_CHECKING:
    from trapi_object_modeling.auxiliary_graph import AuxiliaryGraphsDict
from trapi_object_modeling.utils.object_base import (
    Location,
    SemanticValidationError,
    SemanticValidationResult,
    SemanticValidationWarningList,
    TOMBaseObject,
)
from trapi_object_modeling.utils.semantic_validation import (
    always_valid,
    extend_location,
)


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class PathBinding(TOMBaseObject):
    """A instance of PathBinding is a single binding of an input QueryGraph path (the key to this object) with the AuxiliaryGraph id containing a list of edges in the path.

    The Auxiliary Graph does not convey any order of edges in the path.
    """

    id: AuxGraphID
    """The key identifier of a specific auxiliary graph."""

    @override
    def semantic_validate(
        self,
        location: Location | None = None,
        aux_graphs: AuxiliaryGraphsDict | None = None,
        **kwargs: Any,
    ) -> SemanticValidationResult:
        if aux_graphs is not None and self.id not in aux_graphs:
            return SemanticValidationWarningList(), [
                SemanticValidationError(
                    f"Bound auxiliary graph `{self.id}` is not present in auxiliary_graphs.",
                    extend_location(location, "id"),
                )
            ]
        return always_valid()
