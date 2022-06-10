import os
import unittest
from .test_helper import get_test_files_path
from unittest import mock
from secure_squash_root.file_op import read_from
from secure_squash_root.efi import file_matches_slot, sign, \
    create_efi_executable, build_and_sign_kernel

TEST_FILES_DIR = get_test_files_path("efi")


class EfiTest(unittest.TestCase):

    def test__file_matches_slot(self):

        def wrapper(path: str, slot: str):
            file = os.path.join(TEST_FILES_DIR, path)
            content_before = read_from(file)
            result = file_matches_slot(file, slot)
            self.assertEqual(content_before, read_from(file),
                             "objcopy modified file (breaks secure boot)")
            return result

        self.assertTrue(wrapper("stub_slot_a.efi", "a"))
        self.assertFalse(wrapper("stub_slot_a.efi", "b"))
        self.assertTrue(wrapper("stub_slot_b.efi", "b"))
        self.assertFalse(wrapper("stub_slot_b.efi", "a"))

        self.assertFalse(wrapper("stub_slot_unkown.efi", "a"))
        self.assertFalse(wrapper("stub_slot_unkown.efi", "b"))

    @mock.patch("secure_squash_root.efi.exec_binary")
    def test__sign(self, mock):
        sign("my/key/dir", "my/in/file", "my/out/file")
        mock.assert_called_once_with(
            ["sbsign",
             "--key", "my/key/dir/db.key",
             "--cert", "my/key/dir/db.crt",
             "--output", "my/out/file",
             "my/in/file"])

    @mock.patch("secure_squash_root.efi.exec_binary")
    def test__create_efi_executable(self, mock):
        create_efi_executable(
            "/my/stub.efi", "/tmp/cmdline", "/usr/vmlinuz",
            "/tmp/initramfs.img", "/tmp/file.efi")
        mock.assert_called_once_with([
            'objcopy',
            '--add-section', '.osrel=/etc/os-release',
            '--change-section-vma', '.osrel=0x20000',
            '--add-section', '.cmdline=/tmp/cmdline',
            '--change-section-vma', '.cmdline=0x30000',
            '--add-section', '.linux=/usr/vmlinuz',
            '--change-section-vma', '.linux=0x2000000',
            '--add-section', '.initrd=/tmp/initramfs.img',
            '--change-section-vma', '.initrd=0x3000000',
            '/my/stub.efi', '/tmp/file.efi'])

    def test__build_and_sign_kernel(self):
        all_mocks = mock.Mock()
        base = "secure_squash_root.efi"
        config = {
            "DEFAULT": {
                "CMDLINE": "rw encrypt=/dev/sda2 quiet",
                "SECURE_BOOT_KEYS": "/etc/securebootkeys",
                "EFI_STUB": "/usr/lib/systemd/mystub.efi",
            }
        }
        call = mock.call

        with mock.patch("{}.sign".format(base),
                        new=all_mocks.efi.sign), \
             mock.patch("{}.create_efi_executable".format(base),
                        new=all_mocks.efi.create_efi_executable), \
             mock.patch("{}.write_str_to".format(base),
                        new=all_mocks.write_str_to):
            build_and_sign_kernel(config, "/boot/vmlinuz",
                                  "/tmp/initramfs.img", "a",
                                  "567myhash234", "/tmp/file.efi",
                                  "tmpfsparam")
            self.assertEqual(
                all_mocks.mock_calls,
                [call.write_str_to("/tmp/secure_squash_root/cmdline",
                                   ("rw encrypt=/dev/sda2 quiet tmpfsparam "
                                    "secure_squash_root_slot=a "
                                    "secure_squash_root_hash=567myhash234")),
                 call.efi.create_efi_executable(
                     "/usr/lib/systemd/mystub.efi",
                     "/tmp/secure_squash_root/cmdline",
                     "/boot/vmlinuz", "/tmp/initramfs.img", "/tmp/file.efi"),
                 call.efi.sign("/etc/securebootkeys", "/tmp/file.efi",
                               "/tmp/file.efi")])

            all_mocks.reset_mock()

            build_and_sign_kernel(config, "/usr/lib/vmlinuz-lts",
                                  "/boot/initramfs_fallback.img", "b",
                                  "853anotherhash723", "/tmporary/dir/f.efi",
                                  "")
            self.assertEqual(
                all_mocks.mock_calls,
                [call.write_str_to(
                     "/tmp/secure_squash_root/cmdline",
                     ("rw encrypt=/dev/sda2 quiet  secure_squash_root_slot=b "
                      "secure_squash_root_hash=853anotherhash723")),
                 call.efi.create_efi_executable(
                         "/usr/lib/systemd/mystub.efi",
                         "/tmp/secure_squash_root/cmdline",
                     "/usr/lib/vmlinuz-lts",
                     "/boot/initramfs_fallback.img",
                     "/tmporary/dir/f.efi"),
                 call.efi.sign("/etc/securebootkeys",
                               "/tmporary/dir/f.efi",
                               "/tmporary/dir/f.efi")])
