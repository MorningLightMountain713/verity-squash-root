from typing import Optional
from verity_squash_root.config import KERNEL_PARAM_BASE
from string import ascii_lowercase, digits
from secrets import choice


def current_slot(kernel_cmdline: str) -> Optional[str]:
    params = kernel_cmdline.split(" ")
    for p in params:
        if p.startswith("{}_slot=".format(KERNEL_PARAM_BASE)):
            return p[24:].lower()
    return None

def generate_slot() -> str:
    alphabet = ascii_lowercase + digits
    return ''.join(choice(alphabet) for _ in range(8))

def unused_slot(kernel_cmdline: str) -> str:
    curr = current_slot(kernel_cmdline)
    try:
        next_slot = {"a": "b", "b": "a"}
        return next_slot[curr or ""]
    except KeyError:
        return "a"
