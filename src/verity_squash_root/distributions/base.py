import os
import re
from pathlib import Path
from typing import List


class DistributionConfig:

    _modules_dir: Path = Path("/usr/lib/modules")
    __os_id: str = ""
    __os_name: str = ""

    def __init__(self, os_id: str, os_name: str):
        self.__os_id = os_id
        self.__os_name = os_name

    def kernel_to_name(self, kernel: str) -> str:
        raise NotImplementedError("Base class")

    def display_name(self) -> str:
        return self.__os_name

    def efi_dirname(self) -> str:
        return self.__os_id

    def vmlinuz(self, kernel: str) -> Path:
        return self._modules_dir / kernel / "vmlinuz"

    def list_kernels(self) -> List[str]:
        def int_or_str(e):
            try:
                return int(e)
            except ValueError:
                return e

        def human_sort(e):
            return [int_or_str(a)
                    for a in re.split('([0-9]+)', e)]

        kernels = sorted([k.name for k in self._modules_dir.iterdir()],
                         reverse=True, key=human_sort)

        # VSR_KERNEL_VERSIONS (comma-separated), when set, limits the build
        # to those kernels; unset or empty builds every installed kernel.
        only = os.environ.get("VSR_KERNEL_VERSIONS", "").strip()
        if only:
            wanted = {v.strip() for v in only.split(",") if v.strip()}
            kernels = [k for k in kernels if k in wanted]

        return kernels
