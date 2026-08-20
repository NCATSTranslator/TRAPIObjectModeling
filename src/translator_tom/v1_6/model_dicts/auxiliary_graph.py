from __future__ import annotations

from typing_extensions import TypedDict

from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash
from translator_tom.utils.shared import AuxGraphID, EdgeID
from translator_tom.v1_6.model_dicts.attribute import AttributeDict, AttributeDictUtil
from translator_tom.v1_6.models.auxiliary_graph import AuxiliaryGraph

__all__ = ["AuxiliaryGraphDict", "AuxiliaryGraphDictUtil", "AuxiliaryGraphsDict"]


class AuxiliaryGraphDict(TypedDict):
    edges: list[EdgeID]
    attributes: list[AttributeDict]


AuxiliaryGraphsDict = dict[AuxGraphID, AuxiliaryGraphDict]


class AuxiliaryGraphDictUtil(DictUtil[AuxiliaryGraphDict]):
    """Utility methods for `AuxiliaryGraphDict`, mirroring those on the `AuxiliaryGraph` model."""

    _model = AuxiliaryGraph

    @classmethod
    def hash(cls, obj: AuxiliaryGraphDict) -> str:
        """Hash matching `AuxiliaryGraph.hash` (unordered edges plus attributes)."""
        return tomhash(
            (
                frozenset(obj["edges"]),
                frozenset(AttributeDictUtil.hash(a) for a in obj["attributes"]),
            )
        )

    @staticmethod
    def normalize(
        auxiliary_graph: AuxiliaryGraphDict, mapping: dict[EdgeID, EdgeID]
    ) -> None:
        """Normalize the auxiliary graph given a mapping of old:new EdgeIDs."""
        auxiliary_graph["edges"] = [
            mapping.get(edge_id, edge_id) for edge_id in auxiliary_graph["edges"]
        ]

    @staticmethod
    def normalize_aux_dict(
        auxiliary_graphs_dict: AuxiliaryGraphsDict, mapping: dict[EdgeID, EdgeID]
    ) -> None:
        """Normalize an AuxiliaryGraphsDict given a mapping of old:new EdgeIDs."""
        for auxg in auxiliary_graphs_dict.values():
            AuxiliaryGraphDictUtil.normalize(auxg, mapping)

    @staticmethod
    def update(auxiliary_graph: AuxiliaryGraphDict, other: AuxiliaryGraphDict) -> None:
        """Update the auxiliary graph in-place using the other."""
        if (not auxiliary_graph["attributes"]) and other["attributes"]:
            auxiliary_graph["attributes"] = other["attributes"]
        elif auxiliary_graph["attributes"] and other["attributes"]:
            AttributeDictUtil.merge_attribute_lists(
                auxiliary_graph["attributes"], other["attributes"]
            )

    @staticmethod
    def merge_dictionaries(old: AuxiliaryGraphsDict, new: AuxiliaryGraphsDict) -> None:
        """Merge the new auxiliary graphs into the existing auxiliary graphs."""
        for aux_id, graph in new.items():
            if aux_id in old:
                AuxiliaryGraphDictUtil.update(old[aux_id], graph)
            else:
                old[aux_id] = graph
