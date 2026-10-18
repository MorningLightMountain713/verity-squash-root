import os
import unittest
from pathlib import Path
from unittest import mock
from verity_squash_root.distributions.base import DistributionConfig


class BaseDistributionTest(unittest.TestCase):

    @mock.patch("verity_squash_root.distributions."
                "base.DistributionConfig._modules_dir")
    def test__list_kernels__only(self, modules):
        modules.iterdir.return_value = [Path("/usr/lib/modules/6.1-a"),
                                        Path("/usr/lib/modules/7.0-flux"),
                                        Path("/usr/lib/modules/7.0-b")]
        distri = DistributionConfig("debian", "Debian")
        with mock.patch.dict(os.environ,
                             {"VSR_KERNEL_VERSIONS": " 7.0-flux, 6.1-a"}):
            self.assertEqual(distri.list_kernels(), ["7.0-flux", "6.1-a"])
        with mock.patch.dict(os.environ, {"VSR_KERNEL_VERSIONS": ""}):
            self.assertEqual(distri.list_kernels(),
                             ["7.0-flux", "7.0-b", "6.1-a"])
