from string import ascii_lowercase, digits
from secrets import choice


def generate_slot() -> str:
    alphabet = ascii_lowercase + digits
    return ''.join(choice(alphabet) for _ in range(8))
