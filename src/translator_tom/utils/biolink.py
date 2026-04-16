import bmt
from bmt import utils

from translator_tom.utils.config import TRAPI_CONFIG

biolink = bmt.Toolkit(
    schema=f"https://raw.githubusercontent.com/biolink/biolink-model/refs/tags/v{TRAPI_CONFIG.biolink_version}/biolink-model.yaml",
    predicate_map=f"https://raw.githubusercontent.com/biolink/biolink-model/refs/tags/v{TRAPI_CONFIG.biolink_version}/predicate_mapping.yaml",
)


def get_formatted(element_str: str) -> str | None:
    """Get the formatted form of an element.

    Returns None if the given str is not a valid element.
    """
    element = biolink.get_element(element_str)
    if element is not None:
        return utils.format_element(element)


is_qualifier = biolink.is_qualifier
is_symmetric = biolink.is_symmetric
is_predicate = biolink.is_predicate
is_category = biolink.is_category
get_element = biolink.get_element
get_descendents = biolink.get_descendants
get_ancestors = biolink.get_ancestors
