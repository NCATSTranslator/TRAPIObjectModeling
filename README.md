# TRAPIObjectModeling

A repository for code and issues related to efforts to develop and benchmark a successor for reasoner-pydantic to be used in the new Translator architecture.

## TODO

- [x] Fix performance issues caused by `Attribute`, `RetrievalSource`, and (less so) `Qualifier`
- [ ] Write pytests to check that parsing and dumping works
- [ ] Go through and add examples/etc. using pydantic field annotations
- [ ] Link all concepts together as appropriate
- [ ] Create an `__init__.py` so all items may be imported directly
- [ ] Add hash methods for everything which needs to be hashable
- [ ] Add utility methods to parity with reasoner-pydantic
- [ ] Create a utility mixin so each object can be parsed/dumped without creating a new type adapter
- [ ] Create advanced validation methods for higher levels of validation
- [ ] Add regex validation where it's used in the spec
- [ ] Add advanced validation and utility methods for CURIEs and biolink interactions

## Design Decisions

### Implicit Enums

In some sections (such as `knowledge_type`), only certain values are used by existing systems, despite the field being an open string. In these cases I have added the implictly defined enum so in TOM it is explicit, as this may help to catch early validation errors. This does technically bring TOM out of sync with TRAPI, so it's worth group consideration.

### Lenient interpretation of `additionalProperties: false`

In OpenAPI, `additionalProperties` governs whether an object may have extra properties not defined in the spec. It can be either `true` or `false`. In Pydantic, we can use `allow`, `ignore`, or `forbid`. I have elected to use `ignore` in places where the yaml specification states `additionalProperties: false` such that disallowed extra properties are dropped, rather than raising a validation error, prioritizing answering queries over policing their correctness. However, this does mean that disallowed extra properties are dropped silently, which could make spotting certain problems in non-TOM applications harder.

### Use of `NewType`

Several items have made use of python's `NewType` functionality, where you'd normally expect a string. These are intended to reduce the possibility of mistakes, and can be swapped out with classes that contain more explicit validation in the future if we desire (you'll notice a `curie.py` that doesn't do anything...that was a digression toward trying to properly spec a CURIE validator from the original specs). These newtypes may present an annoyance to the developer, so it's worth discussing if they're worthwhile.
