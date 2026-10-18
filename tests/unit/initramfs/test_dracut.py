import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

from verity_squash_root.initramfs.dracut import Dracut


class DracutTest(unittest.TestCase):
    def test__file_name(self):
        distri = Mock()
        dracut = Dracut(distri)
        res = dracut.file_name("5.17.2")
        assert distri.mock_calls == [call.kernel_to_name("5.17.2")]
        assert res == distri.kernel_to_name()

    def test__display_name(self):
        distri = Mock()
        distri.display_name.return_value = "Debian"
        distri.kernel_to_name.return_value = "hardened-linux"
        dracut = Dracut(distri)
        res = dracut.display_name("5.17.2")
        assert distri.mock_calls == [call.kernel_to_name("5.17.2"), call.display_name()]
        assert res == "Debian Hardened linux"

    @patch("verity_squash_root.initramfs.dracut.exec_binary")
    def test__build_initramfs(self, exec_mock):
        distri = Mock()
        dracut = Dracut(distri)
        result = dracut.build_initramfs("5.17.2", Path("/work"))
        assert result == Path("/work/5.17.2.image")
        assert distri.mock_calls == []
        assert exec_mock.mock_calls == [
            call(
                [
                    "dracut",
                    "--kver",
                    "5.17.2",
                    "--no-uefi",
                    "--early-microcode",
                    "--add",
                    "verity-squash-root",
                    "/work/5.17.2.image",
                ]
            )
        ]
