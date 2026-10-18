import unittest
from pathlib import Path
from unittest import mock
from tests.unit.helpers import PROJECT_ROOT
from verity_squash_root.config import config_str_to_stripped_arr, \
    read_config


class ConfigTest(unittest.TestCase):

    def test__config_str_to_stripped_arr(self):
        self.assertEqual(
            config_str_to_stripped_arr(
                " var/!(lib) ,/mnt/test\n,another/dir/ ,testdir"),
            ["var/!(lib)", "/mnt/test", "another/dir/", "testdir"])

    def test__config_str_to_stripped_arr__empty(self):
        self.assertEqual(config_str_to_stripped_arr(""), [])
        self.assertEqual(config_str_to_stripped_arr(" , /opt ,"), ["/opt"])

    @mock.patch("verity_squash_root.config.ConfigParser")
    def test__read_config(self, cp_mock):
        result = read_config()
        cp_mock.assert_called_once_with(default_section="DO_NOT_USE_DEFAULTS")
        self.assertEqual(cp_mock.mock_calls, [
            mock.call(default_section="DO_NOT_USE_DEFAULTS"),
            mock.call().read(
                PROJECT_ROOT / "src/verity_squash_root/default_config.ini"),
            mock.call().read(
                Path('/usr/share/verity_squash_root/default.ini')),
            mock.call().read(Path('/etc/verity_squash_root/config.ini'))])
        self.assertEqual(result, cp_mock())
