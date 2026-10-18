from secrets import choice
from string import ascii_lowercase, digits


def generate_slot() -> str:
    alphabet = ascii_lowercase + digits
    return "".join(choice(alphabet) for _ in range(8))
