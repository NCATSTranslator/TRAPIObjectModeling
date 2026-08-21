"""Vendor the biolink schema files used by `translator_tom.utils.biolink`.

Downloads `predicate_mapping.yaml`, `biolink-model.yaml`, andthe model's relative
`imports` (e.g. `attributes.yaml` in biolink 4.4.x), writing them under
`src/translator_tom/data/biolink/<version>/`.

Bundling these lets the toolkit load offline and skips GitHub http fetches on import.

`SchemaView` resolves relative imports against the schema file's own directory,
so relative imports must be included.

Usage:
    task vendor:biolink              # uses TRAPI_CONFIG.biolink_version
    task vendor:biolink -- 4.4.4     # explicit version
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.request import urlopen

import yaml


def _default_version() -> str:
    # Deferred so passing an explicit version never imports the package.
    from translator_tom.utils.config import TRAPI_CONFIG  # noqa: PLC0415

    return TRAPI_CONFIG.biolink_version


def _fetch(base: str, filename: str, dest: Path) -> str:
    """Download `{base}/{filename}` into `dest` and return its text."""
    print(f"Fetching {base}/{filename}")
    with urlopen(f"{base}/{filename}") as response:
        text = response.read().decode()
    (dest / filename).write_text(text)
    print(f"  wrote {dest / filename} ({len(text) // 1024} KB)")
    return text


def _relative_imports(schema_text: str) -> list[str]:
    """Return relative import names (CURIE-prefixed imports like `linkml:types` skipped)."""
    doc = yaml.safe_load(schema_text) or {}
    return [imp for imp in (doc.get("imports") or []) if ":" not in imp]


def vendor(version: str) -> None:
    """Vendor the full schema import closure for `version` into the package data dir."""
    base = (
        f"https://raw.githubusercontent.com/biolink/biolink-model/refs/tags/v{version}"
    )
    dest = Path(__file__).resolve().parents[1] / "src" / "translator_tom" / "data"
    dest = dest / "biolink" / version
    dest.mkdir(parents=True, exist_ok=True)

    _fetch(base, "predicate_mapping.yaml", dest)

    # Walk the model's relative-import closure (imports omit the .yaml extension).
    seen: set[str] = set()
    queue = ["biolink-model"]
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        queue.extend(_relative_imports(_fetch(base, f"{name}.yaml", dest)))

    print(f"Vendored biolink v{version} into {dest}")


if __name__ == "__main__":
    vendor(sys.argv[1] if len(sys.argv) > 1 else _default_version())
