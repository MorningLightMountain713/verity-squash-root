import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import call
from tests.unit.helpers import create_initramfs_mock, \
    distribution_mock, wrap_tempdir
from verity_squash_root.main import create_squashfs_return_verity_hash, \
    create_image_and_sign_kernel, sign_extra_files


class MainTest(unittest.TestCase):

    def test__create_squashfs_return_verity_hash(self):
        base = "verity_squash_root.main"
        all_mocks = mock.Mock()

        config = {
            "DEFAULT": {
                "INCLUDE_DIRS": "/root/target",
                "EXCLUDE_DIRS": "var/lib,opt/var",
            }
        }

        with (mock.patch("{}.veritysetup_image".format(base),
                         new=all_mocks.veritysetup_image),
              mock.patch("{}.mksquashfs".format(base),
                         new=all_mocks.mksquashfs)):
            result = create_squashfs_return_verity_hash(
                config, Path("/work/test.img"))
            self.assertEqual(
                all_mocks.mock_calls,
                [call.mksquashfs(['/root/target'], ['var/lib', 'opt/var'],
                                 Path('/work/test.img')),
                 call.veritysetup_image(Path('/work/test.img'))])
            self.assertEqual(
                result,
                all_mocks.veritysetup_image())

    def _create_image(self, variants):
        base = "verity_squash_root.main"
        all_mocks = mock.Mock()
        use_slot = "abcd1234"
        root_hash = "f00d"
        work_dir = Path("/work")

        def initrdfunc(kernel, wd):
            return wd / "initramfs_{}.img".format(kernel)

        config = {
            "DEFAULT": {
                "ROOT_MOUNT": "/opt/mnt/root",
                "EFI_PARTITION": "/boot/efi",
                "VARIANTS": variants,
            }
        }
        with (mock.patch("{}.cmdline".format(base),
                         new=all_mocks.cmdline),
              mock.patch("{}.create_squashfs_return_verity_hash".format(base),
                         new=all_mocks.create_squashfs_return_verity_hash),
              mock.patch("{}.write_str_to".format(base),
                         new=all_mocks.write_str_to),
              mock.patch("{}.efi".format(base),
                         new=all_mocks.efi),
              mock.patch("{}.shutil".format(base),
                         new=all_mocks.shutil),
              mock.patch("{}.Path.mkdir".format(base),
                         new=all_mocks.mkdir)):
            distri = distribution_mock()
            initramfs = create_initramfs_mock(distribution_mock())
            initramfs.build_initramfs.side_effect = initrdfunc
            all_mocks.cmdline.generate_slot.return_value = use_slot
            all_mocks.create_squashfs_return_verity_hash.return_value = \
                root_hash
            create_image_and_sign_kernel(config, distri, initramfs,
                                         work_dir, "fluxos", "42")
        return all_mocks, config

    def _efi_calls(self, config, kernel, cmdline_add, out_name):
        tmp_efi = Path("/work/tmp.efi")
        return [
            call.efi.build_and_sign_kernel(
                config,
                Path("/lib64/modules/{}/vmlinuz".format(kernel)),
                Path("/work/initramfs_{}.img".format(kernel)),
                "abcd1234", "f00d", tmp_efi, Path("/work"),
                cmdline_add, "fluxos", "42"),
            call.shutil.move(
                tmp_efi,
                Path("/boot/efi/EFI/verity_squash_root/ArchEfi") / out_name)]

    def test__create_image_and_sign_kernel__persistent(self):
        all_mocks, config = self._create_image("persistent")
        self.assertEqual(
            all_mocks.mock_calls,
            [call.cmdline.generate_slot(),
             call.mkdir(parents=True, exist_ok=True),
             call.create_squashfs_return_verity_hash(
                 config, Path('/work/tmp.squashfs')),
             call.write_str_to(Path('/opt/mnt/root/root_hash'), "f00d")]
            + self._efi_calls(config, "5.19", "", "linux.efi")
            + self._efi_calls(config, "5.14", "", "linux-lts.efi")
            + [call.shutil.move(
                   Path('/work/tmp.squashfs'),
                   Path('/opt/mnt/root/images/image_abcd1234.squashfs')),
               call.shutil.move(
                   Path('/work/tmp.squashfs.verity'),
                   Path('/opt/mnt/root/images/'
                        'image_abcd1234.squashfs.verity'))])

    def test__create_image_and_sign_kernel__both(self):
        all_mocks, config = self._create_image(" persistent, volatile ")
        efi_calls = [c for c in all_mocks.mock_calls
                     if c[0] in ("efi.build_and_sign_kernel", "shutil.move")]
        volatile = "verity_squash_root_volatile"
        self.assertEqual(
            efi_calls[:8],
            self._efi_calls(config, "5.19", "", "linux.efi")
            + self._efi_calls(config, "5.19", volatile, "linux_tmpfs.efi")
            + self._efi_calls(config, "5.14", "", "linux-lts.efi")
            + self._efi_calls(config, "5.14", volatile,
                              "linux-lts_tmpfs.efi"))

    def test__create_image_and_sign_kernel__volatile(self):
        all_mocks, config = self._create_image("volatile")
        built = [c.args[1] for c in all_mocks.mock_calls
                 if c[0] == "shutil.move" and c.args[0].suffix == ".efi"]
        self.assertEqual(
            built,
            [Path("/boot/efi/EFI/verity_squash_root/ArchEfi/linux_tmpfs.efi"),
             Path("/boot/efi/EFI/verity_squash_root/ArchEfi/"
                  "linux-lts_tmpfs.efi")])

    @wrap_tempdir
    def test__sign_extra_files(self, tempdir):
        base = "verity_squash_root.main"
        all_mocks = mock.Mock()
        systemd_out = Path("{}/EFI/systemd/systemd-bootx64.efi".format(
            tempdir))
        fwupd_out = Path("{}/EFI/fwupd/fwupd.efi".format(tempdir))
        config = {
            "EXTRA_SIGN": {
                "systemd": "/usr/lib/systemd/boot/efi/systemd-bootx64.efi => "
                           "{}".format(systemd_out),
                "fwupd": "/usr/lib/fwupd/fwupd.efi => {}".format(fwupd_out),
            }
        }
        with mock.patch("{}.efi".format(base), new=all_mocks.efi):
            sign_extra_files(config)
            self.assertTrue(systemd_out.resolve().parent.is_dir())
            self.assertTrue(fwupd_out.resolve().parent.is_dir())
            self.assertEqual(
                all_mocks.mock_calls,
                [call.efi.sign(
                     Path("/usr/lib/systemd/boot/efi/systemd-bootx64.efi"),
                     systemd_out),
                 call.efi.sign(Path("/usr/lib/fwupd/fwupd.efi"),
                               fwupd_out)])

    def test__sign_extra_files__exception(self):
        base = "verity_squash_root.main"
        all_mocks = mock.Mock()
        config = {
            "EXTRA_SIGN": {
                "systemd": "/usr/lib/systemd/boot/efi/systemd-bootx64.efi => "
                           " /systemd-bootx64.efi",
                "fwupd": "/usr/lib/fwupd/fwupd.efi",
                "test": "/x.efi => /y.efi",
            }
        }
        with mock.patch("{}.efi".format(base), new=all_mocks.efi):
            with self.assertRaises(ValueError) as e:
                sign_extra_files(config)
            self.assertEqual(
                str(e.exception),
                "extra signing files need to be specified as\n"
                "name = SOURCE => DEST")
            self.assertEqual(
                all_mocks.mock_calls,
                [call.efi.sign(
                     Path("/usr/lib/systemd/boot/efi/systemd-bootx64.efi"),
                     Path("/systemd-bootx64.efi"))])
