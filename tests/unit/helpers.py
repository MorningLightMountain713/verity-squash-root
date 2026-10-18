import shutil
import tempfile
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def get_test_files_path(extra: str) -> Path:
    return Path(__file__).resolve().parent / "files" / extra


def wrap_tempdir(func):
    def f(*args, **kwargs):
        tempdir = Path(tempfile.mkdtemp())
        try:
            return func(*args, **kwargs, tempdir=tempdir)
        finally:
            shutil.rmtree(tempdir)

    return f


def distribution_mock():
    obj_kernel = {"5.19": "linux", "5.14": "linux-lts"}

    def vmlinuz(kernel):
        return Path("/lib64/modules/{}/vmlinuz".format(kernel))

    def kernel_to_name(kernel):
        return obj_kernel[kernel]

    distri_mock = mock.Mock()
    distri_mock.list_kernels.return_value = ["5.19", "5.14"]
    distri_mock.efi_dirname.return_value = "ArchEfi"
    distri_mock.display_name.return_value = "Arch"
    distri_mock.vmlinuz.side_effect = vmlinuz
    distri_mock.kernel_to_name.side_effect = kernel_to_name
    return distri_mock


def create_initramfs_mock(distri):
    initramfs_mock = mock.Mock()

    def file_name(kernel):
        return distri.kernel_to_name(kernel)

    def display_name(kernel):
        return "Display {}".format(
            distri.kernel_to_name(kernel).capitalize())

    initramfs_mock.file_name.side_effect = file_name
    initramfs_mock.display_name.side_effect = display_name
    return initramfs_mock
