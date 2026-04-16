# TRAPIObjectModeling

A repository for code and issues related to efforts to develop and benchmark a successor for reasoner-pydantic to be used in the new Translator architecture.

## TODO

The time to beat in the original implementation was 0.007s Small, 0.05s Med, and 1.1s Large. Additional implementation may lengthen these, but it should be kept close.

- [x] Fix performance issues caused by `Attribute`, `RetrievalSource`, and (less so) `Qualifier`
- [ ] Write pytests to check that parsing and dumping works
- [ ] Go through and add examples/etc. using pydantic field annotations
- [x] Link all concepts together as appropriate
- [x] Create an `__init__.py` so all items may be imported directly
- [x] Add hash methods for everything which needs to be hashable
- [ ] Add utility methods to parity with reasoner-pydantic
- [x] Create a utility mixin so each object can be parsed/dumped without creating a new type adapter
- [x] Create advanced validation methods for higher levels of validation
- [x] Add regex validation where it's used in the spec
- [x] Add advanced validation and utility methods for CURIEs and biolink interactions

## Design Decisions

### Implicit Enums

In some sections (such as `knowledge_type`), only certain values are used by existing systems, despite the field being an open string. In these cases I have added the implictly defined enum so in TOM it is explicit, as this may help to catch early validation errors. This does technically bring TOM out of sync with TRAPI, so it's worth group consideration.

### Literal over Enum

Python Literals are slightly faster for serialization, so internally, literals are used. Enums are still provided for ease of use.

### Lenient interpretation of `additionalProperties: false`

In OpenAPI, `additionalProperties` governs whether an object may have extra properties not defined in the spec. It can be either `true` or `false`. In Pydantic, we can use `allow`, `ignore`, or `forbid`. I have elected to use `ignore` in places where the yaml specification states `additionalProperties: false` such that disallowed extra properties are dropped, rather than raising a validation error, prioritizing answering queries over policing their correctness. However, this does mean that disallowed extra properties are dropped silently, which could make spotting certain problems in non-TOM applications harder.

### Using None where None is allowed, despite default

Some properties are non-required, but default to an empty list. I'm setting these as None, to save serialized space. This is in-line with intended TRAPI 2.0 changes, and doesn't break interoperability.


### Differences from reasoner-pydantic

- Knowledge Node hash does not take `attributes` or `categories` into account
- MetaATtribute hash does not take into account name fields

### Open questions

- Should `Attribute.meets_constraint()` error if the value is incompatible with the operator?
