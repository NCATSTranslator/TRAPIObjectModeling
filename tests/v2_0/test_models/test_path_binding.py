"""Tests for translator_tom.v2_0.models.path_binding."""

import pytest
from pydantic import ValidationError

from translator_tom import PathBinding


class TestPathBinding:
    def test_required_field(self):
        pb = PathBinding(ids=["aux-1"])
        assert pb.ids == ["aux-1"]

    def test_ids_required(self):
        with pytest.raises(ValidationError):
            PathBinding()  # type: ignore[call-arg]

    def test_ids_min_length(self):
        with pytest.raises(ValidationError):
            PathBinding(ids=[])


class TestPathBindingHash:
    def test_deterministic(self):
        a = PathBinding(ids=["aux-1"])
        b = PathBinding(ids=["aux-1"])
        assert a.hash() == b.hash()

    def test_id_order_does_not_matter(self):
        a = PathBinding(ids=["aux-1", "aux-2"])
        b = PathBinding(ids=["aux-2", "aux-1"])
        assert a.hash() == b.hash()
