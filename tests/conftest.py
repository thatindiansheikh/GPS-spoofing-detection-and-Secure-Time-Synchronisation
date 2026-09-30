"""Shared test helpers.

Sentences are built with a checksum helper rather than pasted as literals, so
that a fixture cannot silently become a checksum-failure test by accident.
"""

from __future__ import annotations

import pytest

from gpstrust.nmea.parser import compute_checksum


def nmea(body: str) -> str:
    """Wrap a sentence body ('GPGGA,...') into a framed, checksummed sentence."""
    return f"${body}*{compute_checksum(body):02X}"


@pytest.fixture
def make_sentence():
    return nmea


# A clean fix cycle in the order a u-blox receiver emits it.
CLEAN_CYCLE = [
    nmea("GPGGA,123519.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,"),
    nmea("GPGSA,A,3,04,05,09,12,24,,,,,,,,2.5,0.9,2.1"),
    nmea("GPGSV,2,1,08,01,40,083,46,02,17,308,41,12,07,344,39,14,22,228,45"),
    nmea("GPGSV,2,2,08,15,60,058,43,17,10,148,38,18,82,113,47,20,25,033,40"),
    nmea("GPRMC,123519.00,A,4807.0380,N,01131.0000,E,0.06,84.4,230394,3.1,W"),
    nmea("GPVTG,84.4,T,87.5,M,0.06,N,0.11,K"),
]


@pytest.fixture
def clean_cycle():
    return list(CLEAN_CYCLE)
