from __future__ import annotations

from collections import Counter


def extract_reply_patterns(reply_texts: list[str], *, limit: int = 5) -> list[str]:
    phrases: list[str] = []
    for text in reply_texts:
        cleaned = " ".join(text.lower().split())
        if not cleaned:
            continue
        for phrase in (
            "not interested",
            "already have",
            "send info",
            "interested",
            "stop emailing",
        ):
            if phrase in cleaned:
                phrases.append(phrase)
    counts = Counter(phrases)
    return [phrase for phrase, _ in counts.most_common(limit)]
