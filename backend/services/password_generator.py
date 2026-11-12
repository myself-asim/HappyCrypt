from __future__ import annotations

import secrets
import string


AMBIGUOUS = set("Il1O0|`'\"{}[]()/\\,;:.<> ")


def generate_password(
    length: int = 16,
    uppercase: bool = True,
    lowercase: bool = True,
    numbers: bool = True,
    special: bool = True,
    exclude_ambiguous: bool = False,
) -> str:
    length = max(4, min(128, int(length)))
    pools = []
    if lowercase:
        pools.append(string.ascii_lowercase)
    if uppercase:
        pools.append(string.ascii_uppercase)
    if numbers:
        pools.append(string.digits)
    if special:
        pools.append("!@#$%^&*()-_=+[]{};:,.?/\\|~")
    if not pools:
        raise ValueError("Select at least one character set")

    def filter_chars(chars: str) -> str:
        if not exclude_ambiguous:
            return chars
        return "".join(c for c in chars if c not in AMBIGUOUS)

    pools = [filter_chars(p) for p in pools]
    pools = [p for p in pools if p]
    if not pools:
        raise ValueError("No characters available with current options")

    all_chars = "".join(pools)
    # Ensure at least one from each selected pool when length allows
    password_chars = []
    for p in pools:
        if len(password_chars) < length:
            password_chars.append(secrets.choice(p))
    while len(password_chars) < length:
        password_chars.append(secrets.choice(all_chars))
    # Shuffle securely
    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]
    return "".join(password_chars[:length])
