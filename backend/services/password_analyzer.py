from __future__ import annotations

import math
import re
from collections import Counter

COMMON_PASSWORDS = {
    "password", "123456", "123456789", "qwerty", "abc123", "password1", "111111",
    "123123", "admin", "letmein", "welcome", "iloveyou", "monkey", "dragon",
    "master", "sunshine", "princess", "football", "login", "passw0rd"
}


def _fallback_score(password: str) -> tuple[int, list[str]]:
    issues = []
    if not password:
        return 0, ["Password is empty"]
    length = len(password)
    classes = sum([
        any(c.islower() for c in password),
        any(c.isupper() for c in password),
        any(c.isdigit() for c in password),
        any(not c.isalnum() for c in password),
    ])
    score = 0
    # length
    if length >= 16:
        score += 2
    elif length >= 12:
        score += 1
    elif length < 8:
        issues.append("Too short (use at least 12 characters)")
    # diversity
    score += max(0, classes - 1)
    # penalties
    lower = password.lower()
    if lower in COMMON_PASSWORDS:
        score -= 3
        issues.append("Common password")
    if re.search(r"(.)\1{2,}", password):
        score -= 1
        issues.append("Repeated characters")
    sequences = ["abcdefghijklmnopqrstuvwxyz", "0123456789", "qwertyuiop", "asdfghjkl", "zxcvbnm"]
    for seq in sequences:
        for i in range(len(seq) - 3):
            chunk = seq[i:i+4]
            if chunk in lower or chunk[::-1] in lower:
                score -= 1
                issues.append("Sequential pattern")
                break
    # entropy-ish bonus
    pool = 0
    if any(c.islower() for c in password): pool += 26
    if any(c.isupper() for c in password): pool += 26
    if any(c.isdigit() for c in password): pool += 10
    if any(not c.isalnum() for c in password): pool += 32
    if pool:
        entropy = length * math.log2(pool)
        if entropy >= 80: score += 1
        if entropy >= 100: score += 1
    score = max(0, min(4, score))
    if classes < 3:
        issues.append("Add more character types")
    return score, issues


def analyze_password(password: str) -> dict:
    # Try zxcvbn if available
    try:
        from zxcvbn import zxcvbn  # type: ignore
        res = zxcvbn(password or "")
        score = int(res.get("score", 0))  # 0-4
        feedback = res.get("feedback", {}) or {}
        suggestions = feedback.get("suggestions") or []
        warning = feedback.get("warning")
        issues = []
        if warning:
            issues.append(warning)
        issues.extend(suggestions)
    except Exception:
        score, issues = _fallback_score(password or "")

    labels = ["Very Weak", "Weak", "Medium", "Strong", "Very Strong"]
    label = labels[max(0, min(4, score))]
    return {
        "score": score,
        "label": label,
        "length": len(password or ""),
        "has_lower": any(c.islower() for c in (password or "")),
        "has_upper": any(c.isupper() for c in (password or "")),
        "has_digit": any(c.isdigit() for c in (password or "")),
        "has_special": any(not c.isalnum() for c in (password or "")),
        "issues": issues[:6],
    }
