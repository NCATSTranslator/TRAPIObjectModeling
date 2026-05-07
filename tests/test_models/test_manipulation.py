"""Test manipulation."""

from translator_tom import (
    CURIE,
    KnowledgeGraph,
    Message,
    Node,
    NodeBinding,
    QNode,
    Query,
    Result,
)


def test_manipulation():
    """Test manipulation."""
    request: Query = Query.from_dict(
        {
            "message": {
                "query_graph": {
                    "nodes": {"x": {}},
                    "edges": {},
                }
            }
        }
    )

    message: Message = request.message
    message.knowledge_graph = KnowledgeGraph.new()
    message.results = []

    # get query graph node
    assert message.query_graph is not None
    assert message.query_graph.nodes, "Query graph contains no nodes!"
    qnode_id = next(iter(message.query_graph.nodes))

    # add knowledge graph node
    knode: Node = Node.from_dict(dict(categories=["biolink:NamedThing"], attributes=[]))
    knode_id = CURIE("foo:bar")
    message.knowledge_graph.nodes[knode_id] = knode

    # add result
    node_binding: NodeBinding = NodeBinding.from_dict(dict(id=knode_id, attributes=[]))
    result: Result = Result.from_dict(
        dict(
            node_bindings={qnode_id: [node_binding]},
            analyses=[],
            foo="bar",
        )
    )
    message.results.append(result)

    print(message.to_json())


def test_singletons():
    """Test that str-valued `categories` works."""
    _qnode = QNode.from_dict(
        {
            "ids": ["MONDO:0005737"],
            "categories": ["biolink:Disease"],
        }
    )
