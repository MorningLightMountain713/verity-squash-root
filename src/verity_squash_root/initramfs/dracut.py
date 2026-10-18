import os
from pathlib import Path
from verity_squash_root.exec import exec_binary
from verity_squash_root.distributions.base import DistributionConfig


class Dracut:

    def __init__(self, distribution: DistributionConfig):
        self._distribution = distribution

    def file_name(self, kernel: str) -> str:
        return self._distribution.kernel_to_name(kernel)

    def display_name(self, kernel: str) -> str:
        kernel_name = self._distribution.kernel_to_name(
            kernel).replace("-", " ")
        return "{} {}".format(
            self._distribution.display_name(),
            kernel_name.capitalize())

    def build_initramfs(self, kernel: str, work_dir: Path) -> Path:
        initramfs = work_dir / "{}.image".format(kernel)
        # dracut copies /etc/passwd and /etc/group into the initramfs with
        # the process umask; under the 077 the CLI sets, dbus cannot read
        # them (https://github.com/dracut-ng/dracut-ng/issues/1474).
        old_umask = os.umask(0o022)
        try:
            exec_binary(["dracut", "--kver", kernel, "--no-uefi",
                         "--early-microcode", "--add", "verity-squash-root",
                         str(initramfs)])
        finally:
            os.umask(old_umask)
        return initramfs
