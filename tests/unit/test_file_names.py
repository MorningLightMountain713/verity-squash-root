import unittest
from verity_squash_root.file_names import VARIANTS, Variant, \
    configured_variants


def config_with(variants):
    return {"DEFAULT": {"VARIANTS": variants}}


class FileNamesTest(unittest.TestCase):

    def test__variants(self):
        self.assertEqual(VARIANTS["persistent"], Variant("", "", ""))
        self.assertEqual(
            VARIANTS["volatile"],
            Variant("_tmpfs", " tmpfs", "verity_squash_root_volatile"))

    def test__configured_variants(self):
        self.assertEqual(configured_variants(config_with("persistent")),
                         [VARIANTS["persistent"]])
        self.assertEqual(configured_variants(config_with(" volatile ")),
                         [VARIANTS["volatile"]])
        self.assertEqual(
            configured_variants(config_with("persistent,volatile")),
            [VARIANTS["persistent"], VARIANTS["volatile"]])

    def test__configured_variants__invalid(self):
        for value in ["", " , ", "tmpfs", "persistent,both"]:
            with self.assertRaises(ValueError) as e:
                configured_variants(config_with(value))
            self.assertEqual(
                str(e.exception),
                "VARIANTS must list one or more of: persistent, volatile "
                "(got '{}')".format(value))
