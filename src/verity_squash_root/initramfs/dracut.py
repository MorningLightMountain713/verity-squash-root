from pathlib import Path
from typing import List
from verity_squash_root.config import TMPDIR
from verity_squash_root.exec import exec_binary
from verity_squash_root.distributions.base import DistributionConfig
from verity_squash_root.initramfs.base import InitramfsBuilder


class Dracut(InitramfsBuilder):

    def __init__(self, distribution: DistributionConfig):
        self._distribution = distribution

    def file_name(self, kernel: str, preset: str) -> str:
        return self._distribution.kernel_to_name(kernel)

    def display_name(self, kernel: str, preset: str) -> str:
        kernel_name = self._distribution.kernel_to_name(
            kernel).replace("-", " ")
        return "{} {}".format(
            self._distribution.display_name(),
            kernel_name.capitalize())

    def build_initramfs_with_microcode(self, kernel: str,
                                       preset: str) -> Path:
        import os
        merged_initramfs = TMPDIR / "{}-{}.image".format(kernel, preset)
        # Temporarily reset umask so dracut creates /etc/passwd and /etc/group with correct permissions (644)
        # The parent process sets umask to 077 for security of signing materials, but this breaks dbus
        # See: https://github.com/dracut-ng/dracut-ng/issues/1474
        old_umask = os.umask(0o022)
        try:
            exec_binary(["dracut", "--kver", kernel, "--no-uefi",
                         "--early-microcode", "--add", "verity-squash-root",
                         str(merged_initramfs)])
        finally:
            os.umask(old_umask)
        return merged_initramfs

    def list_kernel_presets(self, kernel: str) -> List[str]:
        return [""]
