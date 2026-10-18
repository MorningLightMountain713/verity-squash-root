from pathlib import Path


def write_str_to(path: Path, content: str) -> None:
    path.write_text(content)


def read_from(path: Path) -> bytes:
    return path.read_bytes()


def read_text_from(path: Path) -> str:
    return read_from(path).decode()
