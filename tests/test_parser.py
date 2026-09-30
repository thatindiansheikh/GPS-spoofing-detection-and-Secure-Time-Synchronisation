"""Parser robustness against the kinds of damage real captures contain."""

from __future__ import annotations

from gpstrust.nmea import (
    ParseStats,
    iter_sentences,
    parse_line,
    verify_checksum,
)
from gpstrust.nmea.parser import compute_checksum

from conftest import nmea


def test_checksum_roundtrip():
    body = "GPGGA,123519.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,"
    assert verify_checksum(nmea(body)) is True


def test_checksum_detects_corruption():
    line = nmea("GPGGA,123519.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,")
    # Flip a digit in the payload; the stored checksum no longer matches.
    corrupted = line.replace("4807.0380", "4807.0381")
    assert verify_checksum(corrupted) is False


def test_missing_checksum_is_tolerated_not_rejected():
    stats = ParseStats()
    body = "GPGGA,123519.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,"
    result = parse_line(f"${body}", stats)
    assert result.ok
    assert stats.checksum_missing == 1
    assert stats.checksum_bad == 0


def test_bad_checksum_is_rejected_and_counted():
    stats = ParseStats()
    line = nmea("GPGGA,123519.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,")
    result = parse_line(line.replace("4807.0380", "4807.0381"), stats)
    assert not result.ok
    assert result.error == "checksum_bad"
    assert stats.checksum_bad == 1
    assert stats.bad == 1


def test_truncated_line_does_not_raise():
    stats = ParseStats()
    result = parse_line("$GPGGA,123519.00,4807.03", stats)
    assert not result.ok or result.msg is not None
    assert stats.total == 1


def test_garbage_without_delimiter_is_counted():
    stats = ParseStats()
    result = parse_line("\xff\xfe binary noise here", stats)
    assert result.error == "no_frame"
    assert stats.no_frame == 1


def test_embedded_nulls_are_stripped():
    stats = ParseStats()
    line = nmea("GPGGA,123519.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,")
    result = parse_line("\x00\x00" + line, stats)
    assert result.ok


def test_leading_garbage_before_dollar_is_recovered():
    stats = ParseStats()
    line = nmea("GPRMC,123519.00,A,4807.0380,N,01131.0000,E,0.06,84.4,230394,3.1,W")
    result = parse_line("tail of a previous sentence" + line, stats)
    assert result.ok
    assert result.sentence_type == "RMC"


def test_concatenated_sentences_are_split():
    a = nmea("GPGGA,123519.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,")
    b = nmea("GPRMC,123519.00,A,4807.0380,N,01131.0000,E,0.06,84.4,230394,3.1,W")
    out = list(iter_sentences([a + b]))
    assert len(out) == 2
    assert out[0].startswith("$GPGGA")
    assert out[1].startswith("$GPRMC")


def test_empty_lines_counted_separately_from_errors():
    stats = ParseStats()
    parse_line("", stats)
    parse_line("   \r\n", stats)
    assert stats.empty == 2
    assert stats.bad == 0


def test_unused_sentence_types_are_not_errors():
    stats = ParseStats()
    # GLL is valid NMEA but this pipeline does not consume it.
    parse_line(nmea("GPGLL,4807.0380,N,01131.0000,E,123519.00,A"), stats)
    assert stats.unused == 1
    assert stats.bad == 0


def test_error_rate_reflects_only_real_failures():
    stats = ParseStats()
    good = nmea("GPGGA,123519.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,")
    for _ in range(9):
        parse_line(good, stats)
    parse_line("garbage", stats)
    assert stats.total == 10
    assert abs(stats.error_rate - 0.1) < 1e-9


def test_checksum_is_masked_to_byte():
    # Non-ASCII must not produce a checksum above 0xFF.
    assert 0 <= compute_checksum("abcÿĀ") <= 0xFF
