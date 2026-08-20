from typing import Any

from translator_tom import Result

EXAMPLE_RESULT: dict[str, Any] = {
    "node_bindings": {
        "n1": {"ids": ["CHEBI:6801"]},
        "n2": {"ids": ["MONDO:5148"]},
    },
    "analyses": [
        {
            "resource_id": "infores:test",
            "edge_bindings": {
                "n1n2": {"ids": ["CHEBI:6801-biolink:treats-MONDO:5148"]},
            },
        },
    ],
    "raw_data": ["test"],
}


def test_result_hashable():
    """Check that we can hash a result with extra properties"""

    result_obj = Result.from_dict(EXAMPLE_RESULT)
    result_dict = result_obj.to_dict()

    assert len(result_dict["raw_data"]) == 1
    assert isinstance(result_dict["raw_data"], list)
    assert result_obj.extra_get("raw_data")[0] == "test"
