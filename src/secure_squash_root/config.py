import os
from configparser import ConfigParser
from typing import List


TMPDIR = "/tmp/secure_squash_root"
KERNEL_PARAM_BASE = "secure_squash_root"
CONFIG_FILE = "/etc/{}/config.ini".format(KERNEL_PARAM_BASE)
DISTRI_FILE = os.path.join("/usr/share/", KERNEL_PARAM_BASE, "default.ini")


def config_str_to_stripped_arr(s: str) -> List[str]:
    return [i.strip() for i in s.split(",")]


def read_config() -> ConfigParser:
    config = ConfigParser()
    directory = os.path.dirname(__file__)
    defconfig = os.path.join(directory, "default_config.ini")
    config.read(defconfig)
    config.read(DISTRI_FILE)
    config.read(CONFIG_FILE)
    return config
