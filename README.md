# TRAPIObjectModeling

A repository for code and issues related to efforts to develop and benchmark a successor for reasoner-pydantic to be used in the new Translator architecture.

## TODO

The time to beat in the original implementation was 0.007s Small, 0.05s Med, and 1.1s Large. Additional implementation may lengthen these, but it should be kept close.

- [x] Fix performance issues caused by `Attribute`, `RetrievalSource`, and (less so) `Qualifier`
- [x] Write pytests to check that parsing and dumping works
- [ ] Go through and add examples/etc. using pydantic field annotations
- [x] Link all concepts together as appropriate
- [x] Create an `__init__.py` so all items may be imported directly
- [x] Add hash methods for everything which needs to be hashable
- [x] Add utility methods to parity with reasoner-pydantic
- [x] Create a utility mixin so each object can be parsed/dumped without creating a new type adapter
- [x] Create advanced validation methods for higher levels of validation
- [x] Add regex validation where it's used in the spec
- [x] Add advanced validation and utility methods for CURIEs and biolink interactions

### Release TODOs

- [ ] Beta phase: implement in Retriever and find any friction points/missing functionality/etc.
- [ ] Get feedback on design decisions
- [ ] Bring test coverage up after initial feedback
- [ ] Create a PyPI package

## Design Decisions

### Implicit Enums

In some sections (such as `knowledge_type`), only certain values are used by existing systems, despite the field being an open string. In these cases I have added the implictly defined enum so in TOM it is explicit, as this may help to catch early validation errors. This does technically bring TOM out of sync with TRAPI, so it's worth group consideration.

I avoided doing this in areas where an enum is implied, but am unsure if Translator-wide use respects (e.g. Response.status)

### Literal over Enum

Python Literals are slightly faster for serialization, so internally, literals are used. Enums are still provided for ease of use.

### Using None where None is allowed, despite default

Some properties are non-required, but default to an empty list. I'm setting these as None, to save serialized space. This is in-line with intended TRAPI 2.0 changes, and doesn't break interoperability.

### Hash calc + representation

- Hashing is used in several cases, including KG normalization. We use `stablehash` to ensure hashes are stable, and output hashes as unpadded base64url, with 120 bits truncation, by default. This offers a nice tradeoff of collision safety and hash shortening; all hashes are exactly 20 characters long. It does reduce the immediate recognizeability and readability of hashes to use base64, though, so I thought to raise it for discussion.

### Differences from reasoner-pydantic

- Extra fields do not contribute to hashes
- Knowledge Node hash does not take `attributes` or `categories` into account
- MetaAttribute hash does not take into account name fields
- Message does not auto-normalize, and results do not auto-merge. You have to manually call the appropriate methods.
- BiolinkEntity, BiolinkPredicate, and BiolinkQualifier are now sub-types on the Biolink utility class.
  - This causes one issue: BiolinkPredicate and BiolinkEntity don't show up the JsonSchema generated from these models (but the patterns are preserved )

### Open questions

- Should `AttributeConstraint.met_by()` error if the value is incompatible with the operator?

## Semantic Validation WIP

There's initial tooling for semantic validation. It's not complete, but the general idea is:

1. Import `from translator_tom import semantic_validate`
2. Call `semantic_validate(<some model>)`
3. Get back a list of warnings and a list of errors, with clear and specific descriptions and location tuples

This may end up being seen as redundant given the Reasoner Validator, but it was quick to prototype and could serve slightly-tanget use-cases (or become a core which the validator wraps around).
