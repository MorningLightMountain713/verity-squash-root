from pathlib import Path

import verity_squash_root.parsing as parsing
from verity_squash_root.exec import exec_binary


def mksquashfs(include_dirs: list[str], exclude_dirs: list[str], image: Path):
    all_excluded = ["dev", "proc", "run", "sys", "tmp", *exclude_dirs]
    options = [
        "-reproducible",
        "-xattrs",
        "-wildcards",
        "-noappend",
        # prevents overlayfs corruption on updates
        "-no-exports",
    ]
    cmd = ["mksquashfs", *include_dirs, str(image), *options, "-e"]
    for d in all_excluded:
        sd = d.strip("/")
        p = Path(d)
        if p.is_file():
            cmd += [sd]
        else:
            cmd += [f"{sd}/*"]
            cmd += [f"{sd}/.*"]
    exec_binary(cmd)


def verity_image_path(image: Path) -> Path:
    return image.with_suffix(f"{image.suffix}.verity")


def veritysetup_image(image: Path) -> str:
    cmd = ["veritysetup", "format", str(image), str(verity_image_path(image))]
    result = exec_binary(cmd)
    stdout = result[0].decode()
    info = parsing.info_to_dict(stdout)
    return info["Root hash"]
