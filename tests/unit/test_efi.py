import math
import os
import unittest
from pathlib import Path
from unittest import mock

import pytest

from tests.unit.helpers import get_test_files_path, make_config
from verity_squash_root.efi import (
    build_and_sign_kernel,
    calculate_efi_stub_alignment,
    calculate_efi_stub_end,
    create_efi_executable,
    get_cmdline,
    sign,
    sign_tool,
)

TEST_FILES_DIR = get_test_files_path("efi")


class EfiTest(unittest.TestCase):
    @mock.patch.dict(os.environ, {"VSR_SIGN_TOOL": "/usr/bin/hsm-sign"})
    @mock.patch("verity_squash_root.efi.exec_binary")
    def test__sign(self, mock):
        sign(Path("my/in/file"), Path("my/out/file"))
        mock.assert_called_once_with(["/usr/bin/hsm-sign", "--output", "my/out/file", "my/in/file"])

    def test__sign_tool__unset(self):
        for env in [{}, {"VSR_SIGN_TOOL": " "}]:
            with mock.patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValueError, match=r"^VSR_SIGN_TOOL is not set$"):
                    sign_tool()

    def test__calculate_efi_stub_end(self):
        assert calculate_efi_stub_end(TEST_FILES_DIR / "stub_slot_a.efi") == 74064

    def test__calculate_efi_stub_alignment(self):
        assert calculate_efi_stub_alignment(TEST_FILES_DIR / "stub_slot_a.efi") == 512

    def test__calculate_efi_stub_alignment__not_found(self):
        with pytest.raises(ValueError, match=r"^Efistub SectionAlignment not found$"):
            calculate_efi_stub_alignment(TEST_FILES_DIR / "no_sections_or_info")

    @mock.patch("verity_squash_root.efi.calculate_efi_stub_alignment")
    @mock.patch("verity_squash_root.efi.exec_binary")
    @mock.patch("verity_squash_root.efi.calculate_efi_stub_end")
    def test__create_efi_executable(self, calc_mock, exec_mock, align_mock):
        def align(x):
            return 2048 * math.ceil(x / 2048)

        align_mock.return_value = 2048
        calc_mock.return_value = 74064
        create_efi_executable(
            TEST_FILES_DIR / "stub_slot_a.efi",
            TEST_FILES_DIR / "cmdline",
            TEST_FILES_DIR / "vmlinuz",
            TEST_FILES_DIR / "initrd",
            Path("/tmp/file.efi"),
        )
        align_mock.assert_called_once_with(TEST_FILES_DIR / "stub_slot_a.efi")
        calc_mock.assert_called_once_with(TEST_FILES_DIR / "stub_slot_a.efi")
        osrel_size = Path("/etc/os-release").stat().st_size

        exec_mock.assert_called_once_with(
            [
                "objcopy",
                "--add-section",
                ".osrel=/etc/os-release",
                "--change-section-vma",
                ".osrel=0x12800",
                "--add-section",
                ".cmdline={}".format(TEST_FILES_DIR / "cmdline"),
                "--change-section-vma",
                f".cmdline={hex(align(0x12800 + osrel_size))}",
                "--add-section",
                ".initrd={}".format(TEST_FILES_DIR / "initrd"),
                "--change-section-vma",
                f".initrd={hex(align(0x13000 + osrel_size))}",
                "--add-section",
                ".linux={}".format(TEST_FILES_DIR / "vmlinuz"),
                "--change-section-vma",
                f".linux={hex(align(0x13800 + osrel_size))}",
                str(TEST_FILES_DIR / "stub_slot_a.efi"),
                str(Path("/tmp/file.efi")),
            ]
        )

    def test__get_cmdline(self):
        cmdline = "rw encrypt=/dev/sda2 quiet"
        assert get_cmdline(make_config({"DEFAULT": {"CMDLINE": cmdline}})) == cmdline

    def test__get_cmdline__unset(self):
        for sections in [{"DEFAULT": {}}, {"DEFAULT": {"CMDLINE": ""}}]:
            config = make_config(sections)
            with pytest.raises(ValueError, match=r"^CMDLINE is not configured$"):
                get_cmdline(config)

    def test__build_and_sign_kernel(self):
        all_mocks = mock.Mock()
        base = "verity_squash_root.efi"
        config = make_config(
            {
                "DEFAULT": {
                    "EFI_STUB": "/usr/lib/systemd/mystub.efi",
                }
            }
        )
        call = mock.call
        work = Path("/work")
        identity = '{"system": "fluxos", "version": "42", "slot": "a", "hash": "567myhash234"}'

        with (
            mock.patch(f"{base}.sign", new=all_mocks.efi.sign),
            mock.patch(f"{base}.get_cmdline", new=all_mocks.get_cmdline),
            mock.patch(f"{base}.create_efi_executable", new=all_mocks.efi.create_efi_executable),
            mock.patch(f"{base}.write_str_to", new=all_mocks.write_str_to),
        ):
            all_mocks.get_cmdline.return_value = "rw encrypt=/dev/sda2 quiet"
            build_and_sign_kernel(
                config,
                Path("/boot/vmlinuz"),
                Path("/work/initramfs.img"),
                "a",
                "567myhash234",
                Path("/work/file.efi"),
                work,
                "tmpfsparam",
                "fluxos",
                "42",
            )
            assert all_mocks.mock_calls == [
                call.get_cmdline(config),
                call.write_str_to(
                    Path("/work/cmdline"),
                    "rw encrypt=/dev/sda2 quiet tmpfsparam rw "
                    "verity_squash_root_slot=a "
                    "verity_squash_root_hash=567myhash234",
                ),
                call.write_str_to(Path("/work/system-identity.cred"), identity),
                call.efi.create_efi_executable(
                    Path("/usr/lib/systemd/mystub.efi"),
                    Path("/work/cmdline"),
                    Path("/boot/vmlinuz"),
                    Path("/work/initramfs.img"),
                    Path("/work/file.efi"),
                    credentials=[("system-identity", Path("/work/system-identity.cred"))],
                ),
                call.efi.sign(Path("/work/file.efi"), Path("/work/file.efi")),
            ]

            all_mocks.reset_mock()

            all_mocks.get_cmdline.return_value = "encrypt=/dev/sda2 quiet"
            build_and_sign_kernel(
                config,
                Path("/usr/lib/vmlinuz-lts"),
                Path("/work/initramfs_fallback.img"),
                "b",
                "853anotherhash723",
                Path("/work/f.efi"),
                work,
            )
            assert all_mocks.mock_calls[1] == call.write_str_to(
                Path("/work/cmdline"),
                "encrypt=/dev/sda2 quiet rw verity_squash_root_slot=b "
                "verity_squash_root_hash=853anotherhash723",
            )
