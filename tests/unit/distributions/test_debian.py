import unittest
from pathlib import Path
from unittest import mock

from verity_squash_root.distributions.debian import DebianConfig


class DebianConfigTest(unittest.TestCase):
    def test__efi_dirname(self):
        debian = DebianConfig("ubuntu", "Kali")
        assert debian.efi_dirname() == "ubuntu"

    def test__kernel_to_name(self):
        debian = DebianConfig("debian", "Debian GNU/Linux")
        debian.list_kernels = mock.Mock(return_value=["6.1.13", "5.15.2", "5.4"])
        assert debian.kernel_to_name("6.1.13") == "current"
        assert debian.kernel_to_name("5.15.2") == "old"
        assert debian.kernel_to_name("5.4") == "old_x2"

    def test__vmlinuz(self):
        debian = DebianConfig("debian", "Debian GNU/Linux")
        assert debian.vmlinuz("5.17.2-debian") == Path("/boot/vmlinuz-5.17.2-debian")

    def test__display_name(self):
        debian = DebianConfig("debian", "Debian GNU/Linux")
        assert debian.display_name() == "Debian GNU/Linux"

    @mock.patch("verity_squash_root.distributions.base.DistributionConfig._modules_dir")
    def test__list_kernels(self, mock):
        mock.iterdir.return_value = [
            Path("/usr/lib/modules/5.16.4-amd64"),
            Path("/usr/lib/modules/5.4.2-amd64"),
            Path("/usr/lib/modules/6.0.1-amd64"),
            Path("/usr/lib/modules/5.13.2-amd64"),
        ]
        debian = DebianConfig("debian", "Debian GNU/Linux")
        result = debian.list_kernels()
        mock.iterdir.assert_called_once_with()
        assert result == ["6.0.1-amd64", "5.16.4-amd64", "5.13.2-amd64", "5.4.2-amd64"]
