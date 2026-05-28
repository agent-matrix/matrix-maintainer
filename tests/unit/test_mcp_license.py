from __future__ import annotations

from matrix_codex.mcp.license import classify, decide, detect_from_text


def test_classify_known_permissive() -> None:
    assert classify("MIT") == "permissive"
    assert classify("Apache-2.0") == "permissive"


def test_classify_strong_copyleft() -> None:
    assert classify("GPL-3.0") == "strong-copyleft"
    assert classify("AGPL-3.0") == "strong-copyleft"


def test_classify_restricted() -> None:
    assert classify("SSPL-1.0") == "restricted"
    assert classify("BSL-1.1") == "restricted"


def test_classify_unknown() -> None:
    assert classify(None) == "unknown"
    assert classify("WTFPL") == "unknown"


def test_decide_default_allowlist() -> None:
    d = decide("MIT")
    assert d.allowed is True
    assert d.policy_class == "permissive"


def test_decide_rejects_unknown_by_default() -> None:
    d = decide("WTFPL")
    assert d.allowed is False
    assert d.policy_class == "unknown"


def test_decide_rejects_strong_copyleft_by_default() -> None:
    d = decide("GPL-3.0")
    assert d.allowed is False


def test_decide_allows_strong_copyleft_when_explicit() -> None:
    d = decide("GPL-3.0", allowed_classes=("permissive", "weak-copyleft", "strong-copyleft"))
    assert d.allowed is True


def test_detect_from_text_mit() -> None:
    text = "MIT License\n\nPermission is hereby granted, free of charge, to any person obtaining a copy..."
    assert detect_from_text(text) == "MIT"


def test_detect_from_text_apache() -> None:
    text = "Apache License\nVersion 2.0, January 2004\nhttp://www.apache.org/licenses/"
    assert detect_from_text(text) == "Apache-2.0"


def test_detect_from_text_empty() -> None:
    assert detect_from_text("") is None
