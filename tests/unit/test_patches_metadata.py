from __future__ import annotations

import hashlib

from matrix_codex.patches.metadata import Patch, SCHEMA_VERSION, sha256_hex


DIFF_BYTES = b"diff --git a/foo b/foo\nindex 0..1 100644\n--- a/foo\n+++ b/foo\n@@ -1 +1 @@\n-old\n+new\n"


def test_sha256_hex_consistent() -> None:
    assert sha256_hex(DIFF_BYTES) == hashlib.sha256(DIFF_BYTES).hexdigest()


def test_from_bytes_text() -> None:
    patch = Patch.from_bytes(
        DIFF_BYTES,
        upstream_repo="https://github.com/foo/bar",
        upstream_commit="a" * 40,
        title="add new line",
        mcp_manifest_id="foo-bar",
    )
    assert patch.metadata.schema_version == SCHEMA_VERSION
    assert patch.metadata.id == "p-" + patch.metadata.sha256[:16]
    assert patch.metadata.size_bytes == len(DIFF_BYTES)
    assert patch.body.encoding == "text/utf-8"
    assert patch.metadata.verify(DIFF_BYTES) is True


def test_from_bytes_binary_base64() -> None:
    binary = bytes(range(256))
    patch = Patch.from_bytes(
        binary,
        upstream_repo="https://github.com/foo/bar",
        upstream_commit="b" * 40,
    )
    assert patch.body.encoding == "binary/base64"
    assert patch.body.to_bytes() == binary
    assert patch.metadata.verify(binary)
