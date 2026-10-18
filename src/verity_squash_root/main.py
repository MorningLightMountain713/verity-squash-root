import logging
import shutil
from configparser import ConfigParser
from pathlib import Path

import verity_squash_root.cmdline as cmdline
import verity_squash_root.efi as efi
from verity_squash_root.config import EFI_KERNELS, config_str_to_stripped_arr
from verity_squash_root.distributions.base import DistributionConfig
from verity_squash_root.file_names import configured_variants
from verity_squash_root.file_op import write_str_to
from verity_squash_root.image import (
    mksquashfs,
    verity_image_path,
    veritysetup_image,
)
from verity_squash_root.initramfs.dracut import Dracut


def create_squashfs_return_verity_hash(config: ConfigParser, image: Path) -> str:
    logging.debug(f"Image path: {image}")
    defaults = config["DEFAULT"]
    include_dirs = config_str_to_stripped_arr(defaults["INCLUDE_DIRS"])
    exclude_dirs = config_str_to_stripped_arr(defaults["EXCLUDE_DIRS"])
    logging.info("Creating squashfs...")
    mksquashfs(include_dirs, exclude_dirs, image)
    logging.info("Setup device verity")
    return veritysetup_image(image)


def create_image_and_sign_kernel(
    config: ConfigParser,
    distribution: DistributionConfig,
    initramfs: Dracut,
    work_dir: Path,
    system_name: str = "unknown",
    system_version: str = "0",
):
    variants = configured_variants(config)
    use_slot = cmdline.generate_slot()
    efi_partition = Path(config["DEFAULT"]["EFI_PARTITION"])
    out_dir = efi_partition / EFI_KERNELS / distribution.efi_dirname()
    out_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Using slot {use_slot} for new image")
    root_mount = Path(config["DEFAULT"]["ROOT_MOUNT"])
    image = root_mount / f"images/image_{use_slot}.squashfs"
    tmp_image = work_dir / "tmp.squashfs"
    root_hash = create_squashfs_return_verity_hash(config, tmp_image)
    write_str_to(root_mount / "root_hash", root_hash)
    logging.debug(f"Calculated root hash: {root_hash}")

    for kernel in distribution.list_kernels():
        base_name = initramfs.file_name(kernel)
        display = initramfs.display_name(kernel)
        logging.info(f"Create initramfs for {display}")
        initramfs_path = initramfs.build_initramfs(kernel, work_dir)

        for variant in variants:
            logging.info(f"Processing {display}{variant.label_suffix}")
            tmp_efi_file = work_dir / "tmp.efi"
            efi.build_and_sign_kernel(
                config,
                distribution.vmlinuz(kernel),
                initramfs_path,
                use_slot,
                root_hash,
                tmp_efi_file,
                work_dir,
                variant.cmdline,
                system_name,
                system_version,
            )
            out = out_dir / f"{base_name}{variant.file_suffix}.efi"
            logging.debug(f"Write efi to {out}")
            shutil.move(tmp_efi_file, out)

    # Only replace old image if initramfs was successfully created
    shutil.move(tmp_image, image)
    shutil.move(verity_image_path(tmp_image), verity_image_path(image))


def sign_extra_files(config: ConfigParser):
    extra = config["EXTRA_SIGN"]
    for key in extra.keys():
        logging.info(f"Signing {key}...")
        files = extra[key].split("=>")
        if len(files) != 2:
            raise ValueError("extra signing files need to be specified as\nname = SOURCE => DEST")
        src = Path(files[0].strip())
        dest = Path(files[1].strip())
        logging.debug(f"Sign file '{src}' to '{dest}'")
        dest.resolve().parent.mkdir(parents=True, exist_ok=True)
        efi.sign(src, dest)
