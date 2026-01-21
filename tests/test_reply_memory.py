from __future__ import annotations

from amis_agent.application.services.reply_memory import extract_reply_patterns


def test_extract_reply_patterns():
    replies = [
        "Not interested, thanks.",
        "Please send info.",
        "We already have a solution.",
        "Not interested.",
    ]
    patterns = extract_reply_patterns(replies)
    assert "not interested" in patterns
    assert "send info" in patterns
