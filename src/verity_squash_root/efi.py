import json
import math
import os
from collections import OrderedDict
from configparser import ConfigParser
from pathlib import Path

from verity_squash_root.config import KERNEL_PARAM_BASE
from verity_squash_root.exec import exec_binary
from verity_squash_root.file_op import write_str_to


def sign_tool() -> str:
    # The signer holds the key; it is called as `<tool> --output <out> <in>`.
    tool = os.environ.get("VSR_SIGN_TOOL", "").strip()
    if not tool:
        raise ValueError("VSR_SIGN_TOOL is not set")
    return tool


def sign(in_file: Path, out_file: Path) -> None:
    exec_binary([sign_tool(), "--output", str(out_file), str(in_file)])


def calculate_efi_stub_end(stub: Path) -> int:
    result = exec_binary(["objdump", "-h", str(stub)])
    lines = result[0].decode().split("\n")
    words = lines[-3].split()
    return int(words[2], 16) + int(words[3], 16)


def calculate_efi_stub_alignment(stub: Path) -> int:
    result = exec_binary(["objdump", "-p", str(stub)])
    lines = result[0].decode().split("\n")
    for line in lines:
        words = line.split()
        if len(words) == 2:
            if words[0] == "SectionAlignment":
                return int(words[1], 16)
    raise ValueError("Efistub SectionAlignment not found")


# TODO: use systemd-ukify when Debian 13 is stable
def create_efi_executable(
    stub: Path,
    cmdline_file: Path,
    linux: Path,
    initrd: Path,
    dest: Path,
    credentials: list[tuple[str, Path]] | None = None,
):
    offset = calculate_efi_stub_end(stub)
    alignment = calculate_efi_stub_alignment(stub)
    sections = OrderedDict()
    sections["osrel"] = Path("/etc/os-release")
    sections["cmdline"] = cmdline_file

    # Add credentials (measured into PCR 12) before initrd
    if credentials:
        for cred_name, cred_file in credentials:
            sections[f"cred.{cred_name}"] = cred_file

    sections["initrd"] = initrd
    # place linux at the end so decompressing it in-place does not
    # cause problems:
    # https://github.com/systemd/systemd/commit/
    # 0fa2cac4f0cdefaf1addd7f1fe0fd8113db9360b#commitcomment-84868898
    sections["linux"] = linux

    cmd = ["objcopy"]
    for name, file in sections.items():
        offset = alignment * math.ceil(offset / alignment)
        size = file.stat().st_size
        cmd += [
            "--add-section",
            f".{name}={str(file)}",
            "--change-section-vma",
            f".{name}={hex(offset)}",
        ]
        offset = offset + size
    cmd += [str(stub), str(dest)]
    exec_binary(cmd)


def get_cmdline(config: ConfigParser) -> str:
    con_line = config["DEFAULT"].get("CMDLINE")
    if not con_line:
        raise ValueError("CMDLINE is not configured")
    return con_line


def build_and_sign_kernel(
    config: ConfigParser,
    vmlinuz: Path,
    initramfs: Path,
    slot: str,
    root_hash: str,
    out_file: Path,
    work_dir: Path,
    add_cmdline: str = "",
    system_name: str = "unknown",
    system_version: str = "0",
) -> None:
    # add rw, if root is mounted ro, it cannot be mounted rw later
    slot_cmd = f"{KERNEL_PARAM_BASE}_slot={slot}"
    hash_cmd = f"{KERNEL_PARAM_BASE}_hash={root_hash}"
    commands = [get_cmdline(config), add_cmdline, "rw", slot_cmd, hash_cmd]
    cmdline = " ".join(x for x in commands if x)
    cmdline_file = work_dir / "cmdline"
    write_str_to(cmdline_file, cmdline)

    # Create system identity credential for PCR 12 measurement
    identity = {"system": system_name, "version": system_version, "slot": slot, "hash": root_hash}
    identity_file = work_dir / "system-identity.cred"
    write_str_to(identity_file, json.dumps(identity))

    create_efi_executable(
        Path(config["DEFAULT"]["EFI_STUB"]),
        cmdline_file,
        vmlinuz,
        initramfs,
        out_file,
        credentials=[("system-identity", identity_file)],
    )
    sign(out_file, out_file)
