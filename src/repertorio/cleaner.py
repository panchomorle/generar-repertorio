import re
from typing import Dict, List, Any


def is_tab_line(line_text: str) -> bool:
    """Determine if a line is a guitar tablature line to be filtered out."""
    s = line_text.strip()
    if not s:
        return False
    # Standard guitar string tab line: E|---, B|---, e|---, etc.
    if re.match(r"^[eEaAdDgGbB]\|[-0-9\s/\\~pbh|()xX]+$", s):
        return True
    # General tab pattern with 3 or more hyphens and pipes
    if re.search(r"\|[-]{3,}", s) or re.search(r"[-]{3,}\|", s):
        return True
    return False


def get_line_text(tokens: List[Dict[str, Any]]) -> str:
    """Return the plain text of a tokenized line."""
    return "".join(t["text"] for t in tokens)


def filter_and_clean_lines(lines: List[List[Dict[str, Any]]]) -> List[List[Dict[str, Any]]]:
    """Filter out tab lines and normalize consecutive empty lines."""
    filtered: List[List[Dict[str, Any]]] = []
    consecutive_empty = 0

    for tokens in lines:
        plain_text = get_line_text(tokens)

        # Skip tablature lines
        if is_tab_line(plain_text):
            continue

        # Check for empty lines
        if not plain_text.strip():
            consecutive_empty += 1
            if consecutive_empty <= 1:
                filtered.append([{"text": "", "is_chord": False}])
        else:
            consecutive_empty = 0
            filtered.append(tokens)

    # Strip leading and trailing empty lines
    while filtered and not get_line_text(filtered[0]).strip():
        filtered.pop(0)
    while filtered and not get_line_text(filtered[-1]).strip():
        filtered.pop()

    return filtered
