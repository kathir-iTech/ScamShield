import unicodedata
import re
from typing import Tuple


def normalise(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    return value.lower().strip()


def levenshtein(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    if len(s2) == 0:
        return len(s1)
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            cost = 0 if c1 == c2 else 1
            curr_row.append(min(
                curr_row[j] + 1,
                prev_row[j + 1] + 1,
                prev_row[j] + cost,
            ))
        prev_row = curr_row
    return prev_row[-1]


def digits_only(value: str) -> str:
    return "".join(c for c in value if c.isdigit())


def domain_from_url(url: str) -> str:
    url = normalise(url)
    for prefix in ["http://", "https://", "www."]:
        url = url.replace(prefix, "")
    url = url.split("/")[0]
    url = url.split("?")[0]
    return url
