from configparser import ConfigParser
from typing import List, NamedTuple
from verity_squash_root.config import KERNEL_PARAM_BASE, \
    config_str_to_stripped_arr


class Variant(NamedTuple):
    file_suffix: str
    label_suffix: str
    cmdline: str


# persistent: the overlay's upper layer is a directory on the root
#   partition, so writes survive a reboot.
# volatile: the upper layer is a tmpfs, so every boot starts from the image.
VARIANTS = {
    "persistent": Variant("", "", ""),
    "volatile": Variant("_tmpfs", " tmpfs",
                        "{}_volatile".format(KERNEL_PARAM_BASE)),
}


def configured_variants(config: ConfigParser) -> List[Variant]:
    names = config_str_to_stripped_arr(config["DEFAULT"]["VARIANTS"])
    unknown = [n for n in names if n not in VARIANTS]
    if not names or unknown:
        raise ValueError(
            "VARIANTS must list one or more of: {} (got '{}')".format(
                ", ".join(VARIANTS), config["DEFAULT"]["VARIANTS"]))
    return [VARIANTS[n] for n in names]
