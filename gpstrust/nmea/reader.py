"""Line sources and sentence framing.

Separated from the parser because framing is a transport concern: a captured
log may have lost its line breaks, concatenated two sentences into one line, or
been written in an encoding that no longer round-trips. The parser should see
one candidate sentence at a time regardless of how the file was written.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Iterator

# A candidate sentence runs from a start delimiter up to (but not including)
# the next one. This recovers sentences from logs whose line breaks were lost,
# which is common when a capture is copied through a terminal.
_SENTENCE_RE = re.compile(r"[$!][^$!]*")


def iter_sentences(chunks: Iterable[str]) -> Iterator[str]:
    """Yield individual candidate sentences from arbitrary text chunks.

    Lines containing no delimiter at all are passed through unchanged so the
    parser can count them as framing failures rather than silently dropping
    them; the error rate is a signal we want to keep.
    """
    for chunk in chunks:
        if not chunk:
            continue
        found = _SENTENCE_RE.findall(chunk)
        if found:
            for sentence in found:
                yield sentence.strip()
        else:
            yield chunk.strip()


def read_file(path: str | Path, encoding: str = "utf-8") -> Iterator[str]:
    """Read a capture file, tolerating encoding damage and binary noise.

    errors="replace" rather than "ignore": a replacement character breaks the
    checksum and the line is correctly counted as corrupt, whereas silently
    dropping the byte could turn a damaged sentence into a plausible-looking
    valid one.
    """
    p = Path(path)
    with p.open("r", encoding=encoding, errors="replace", newline=None) as fh:
        for line in fh:
            yield line


def sentences_from_file(path: str | Path, encoding: str = "utf-8") -> Iterator[str]:
    """Convenience: file path straight to framed candidate sentences."""
    yield from iter_sentences(read_file(path, encoding=encoding))
