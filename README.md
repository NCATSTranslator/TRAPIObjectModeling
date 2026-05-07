# TRAPI Object Modeling: `translator_tom`

A library for statically typed, fast serialize/deserialize TRAPI in Python, for Translator-wide use.

Models based on Pydantic provide deserialize with basic validation, serialize, and statically-typed construction with very reasonable performance, as well as utility methods based on architectural descisions, such as message/result/kg/etc. merging and standard TRAPI manipulation.

Allows for easy FastAPI standup.

## Usage

The main ways you interact with a Model are as follows:

- `Model.from_json()` and `Model.to_json()`
- `Model.from_dict()` and `Model.to_dict()`
- `Model.from_msgpack()` and `Model.to_msgpack()`
- Validated instantiation: `Model()`
- Direct construction: `Model.model_construct()`

### JSON Validation

These models can be used for validation of straight JSON:

```python
from translator_tom import Query

query_json = """
{
  "submitter": "TOM tester",
  "message": {
    "query_graph": {
      "nodes": {
        "n0": { "ids": [ "PUBCHEM.COMPOUND:726218" ] },
        "n1": { "ids": [ "NCBIGene:3778" ] }
      },
      "edges": {
        "e0": {
          "subject": "n0",
          "object": "n1",
          "predicates": [ "biolink:related_to" ]
        }
      }
    }
  }
}
"""

query = Query.from_json(query_json)
assert len(query.message.query_graph.nodes) == 2  # True
```

Similarly, you can validate from JSON with a FastAPI endpoint:

```python
from fastapi import FastAPI
from translator_tom import Query

app = FastAPI()

@app.post("/query")
def query(body: Query) -> str:
    return f"Got {len(body.message.query_graph.nodes)} query nodes!"
```

### Dict Validation

You can also validate dicts:

```python
from translator_tom import Query

query_dict = {
  "submitter": "TOM tester",
  "message": {
    "query_graph": {
      "nodes": {
        "n0": { "ids": [ "PUBCHEM.COMPOUND:726218" ] },
        "n1": { "ids": [ "NCBIGene:3778" ] }
      },
      "edges": {
        "e0": {
          "subject": "n0",
          "object": "n1",
          "predicates": [ "biolink:related_to" ]
        }
      }
    }
  }
}

query = Query.from_dict(query_dict)
assert len(query.message.query_graph.nodes) == 2  # True

query = Query(**query_dict)  # Also works (less clear, not recommended)
assert len(query.message.query_graph.nodes) == 2  # True
```

### Construction

There are two ways to construct instances within Python:

The first is just calling the model like any class. This ensures everything you pass is validated (meaning you don't need to construct every model and can just pass dicts, though static type checkers will complain).

```python
from translator_tom import Query

query = Query(
    submitter="TOM tester",
    # Could use types, or just pass a dict (static checkers will complain, though!)
    message={
        "query_graph": {
            "nodes": {
                "n0": {"ids": ["PUBCHEM.COMPOUND:726218"]},
                "n1": {"ids": ["NCBIGene:3778"]},
            },
            "edges": {
                "e0": {
                    "subject": "n0",
                    "object": "n1",
                    "predicates": ["biolink:related_to"],
                }
            },
        }
    },
)
assert len(query.message.query_graph.nodes) == 2  # True
```

Another way is to use `Model.model_construct()`.

> [!WARNING]
> This does no validation, so it's faster, but you **have** to pass correct construction for everything. No types will be coerced to their correct models. Only use it for internal construction where you know everything is already valid (a static type checker such as ty or pylance is highly recommended!). An example:

```python
from translator_tom import Biolink, Curie, Message, QEdge, QNode, Query, QueryGraph

# Using each type provides hints and type checking, making internal TRAPI construction
# safer.
query = Query(
    submitter="TOM tester",
    message=Message(
        query_graph=QueryGraph(
            nodes={
                # Used a helper function to ensure curie formatting (optional)
                "n0": QNode(ids=[Curie("PUBCHEM.COMPOUND", "726218")]),
                "n1": QNode(ids=["NCBIGene:3778"]),
            },
            edges={
                "e0": QEdge(
                    subject="n0",
                    object="n1",
                    # Used a helper function to ensure biolink prefix formatting (optional)
                    predicates=[Biolink("related_to")],
                )
            },
        )
    ),
)
assert len(query.message.query_graph.nodes) == 2  # True
```

### Convenience Methods

TOM provides many convenience methods, similar to those in reasoner-pydantic.

```python
from translator_tom import KnowledgeGraph

my_kg = KnowledgeGraph.new()  # Init an empty knowledge graph

other_kg = get_some_kg()  # Imagine a function returns another KG with data...
_old_new_mapping = other_kg.normalize()  # Normalize edge IDs (keeps a mapping of old->new)

my_kg.update(other_kg, pre_normalized="other")  # Handles merging appropriately, can skip redundant normalization
```

There are many more, it's recommended to look at the models themselves as they are self-documenting (every model has docstrings equivalent to the descriptions in the original spec!). Common examples are `.<field>_list` and `.<field>_dict` for optional container fields for easy iteration without None-guarding, `.new()` for quick instantiation with sensible defaults (mostly of container-like models, but also for LogEntry with automatic timestamping), etc.

More in-depth utility methods include `.normalize()` for Message/KnowledgeGraph/Result/AuxiliaryGraph, `.prune()` for KnowledgeGraph, etc.

### Semantic Validation (WIP)

A very WIP item is Semantic Validation:

```python
from translator_tom.validation import semantic_validate

warnings, errors = semantic_validate(some_model)  # Any TOM model
```

This returns a list of warnings and errors with clear descriptions and tuples describing their locations.

> [!WARNING]
> This feature is WIP and does not do every bit of semantic validation you might expect.

## Design Decisions

There are a view caveats to using TOM, listed below:

### Implicit Enums

In some sections (such as `knowledge_type`), only certain values are used by existing systems, despite the field being an open string. In these cases TOM explicitly defines enums, as this may help to catch early validation errors. Some areas where the TRAPI spec defines short-codes that are not well-policed do not define enums.

### Literal over Enum

Python Literals are slightly faster for serialization, so internally, literals are used. Enums are still provided, largely for documentation access. All literals use the standard names you'd expect from TRAPI, while enums have `Enum` as a suffix.

### Using None where None is allowed, despite default

In TRAPI, some properties are non-required, but default to an empty list. TOM defaults these to None, to save serialized space. This is in-line with intended TRAPI 2.0 changes, and doesn't break interoperability.

### Hash calc + representation

Hashing is used in several cases, including KG normalization. TOM uses `stablehash` to ensure hashes are stable, and outputs hashes as unpadded base64url, with 120 bits truncation, by default. This offers a nice tradeoff of collision safety and hash shortening; all hashes are exactly 20 characters long.

### Differences from reasoner-pydantic

- Extra fields do not contribute to hashes
- Knowledge Node hash does not take `attributes` or `categories` into account
- MetaAttribute hash does not take into account name fields
- Message does not auto-normalize, and results do not auto-merge. You have to manually call the appropriate methods.
- BiolinkEntity, BiolinkPredicate, and BiolinkQualifier are now sub-types on the Biolink utility class.
  - This causes one issue: BiolinkPredicate and BiolinkEntity don't show up the JsonSchema generated from these models (but the patterns are preserved )
