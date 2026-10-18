from configparser import ConfigParser
from pathlib import Path

KERNEL_PARAM_BASE = "verity_squash_root"
CONFIG_DIR = Path(f"/etc/{KERNEL_PARAM_BASE}")
CONFIG_FILE = CONFIG_DIR / "config.ini"
DISTRI_FILE = Path("/usr/share") / KERNEL_PARAM_BASE / "default.ini"
LOG_FILE = Path(f"/var/log/{KERNEL_PARAM_BASE}.log")
EFI_PATH = Path("EFI")
EFI_KERNELS = EFI_PATH / KERNEL_PARAM_BASE


def config_str_to_stripped_arr(s: str) -> list[str]:
    return [i.strip() for i in s.split(",") if i.strip()]


def read_config() -> ConfigParser:
    # defaults will be visible in EXTRA_SIGN and break
    config = ConfigParser(default_section="DO_NOT_USE_DEFAULTS")
    directory = Path(__file__).resolve().parent
    defconfig = directory / "default_config.ini"
    config.read(defconfig)
    config.read(DISTRI_FILE)
    config.read(CONFIG_FILE)
    return config
