# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.1] - 2026-11-20

[2.4.1]: https://github.com/NCATSTranslator/TRAPIObjectModeling/releases/tag/v2.4.1

### Changed

- Streamline deployment workflow

### Fixed

- DictUtils which subclassed other DictUtils resolved wrong TypeAdapters, breaking
  validation
- Add missing get_parameters() to AsyncQueryDictUtil
