import re
import unittest

import pytest

from tests.unit.helpers import make_config
from verity_squash_root.file_names import VARIANTS, Variant, configured_variants


def config_with(variants):
    return make_config({"DEFAULT": {"VARIANTS": variants}})


class FileNamesTest(unittest.TestCase):
    def test__variants(self):
        assert VARIANTS["persistent"] == Variant("", "", "")
        assert VARIANTS["volatile"] == Variant("_tmpfs", " tmpfs", "verity_squash_root_volatile")

    def test__configured_variants(self):
        assert configured_variants(config_with("persistent")) == [VARIANTS["persistent"]]
        assert configured_variants(config_with(" volatile ")) == [VARIANTS["volatile"]]
        assert configured_variants(config_with("persistent,volatile")) == [
            VARIANTS["persistent"],
            VARIANTS["volatile"],
        ]

    def test__configured_variants__invalid(self):
        for value in ["", " , ", "tmpfs", "persistent,both"]:
            expected = f"VARIANTS must list one or more of: persistent, volatile (got '{value}')"
            with pytest.raises(ValueError, match=re.escape(expected)):
                configured_variants(config_with(value))
