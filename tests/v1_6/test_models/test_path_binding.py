"""Tests for translator_tom.v1_6.models.path_binding."""

import pytest
from pydantic import ValidationError

from translator_tom.v1_6 import PathBinding


class TestPathBinding:
    def test_required_field(self):
        pb = PathBinding(id="aux-1")
        assert pb.id == "aux-1"

    def test_id_required(self):
        with pytest.raises(ValidationError):
            PathBinding()  # type: ignore[call-arg]
