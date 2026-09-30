"""NMEA input layer: framing, parsing, and assembly into per-second epochs."""

from .parser import (
    USED_TYPES,
    ParsedLine,
    ParseStats,
    compute_checksum,
    parse_line,
    to_float,
    to_int,
    verify_checksum,
)
from .epoch import Epoch, EpochAssembler, SatelliteView, epochs_from_sentences
from .reader import iter_sentences, read_file, sentences_from_file

__all__ = [
    "USED_TYPES",
    "ParsedLine",
    "ParseStats",
    "compute_checksum",
    "parse_line",
    "to_float",
    "to_int",
    "verify_checksum",
    "Epoch",
    "EpochAssembler",
    "SatelliteView",
    "epochs_from_sentences",
    "iter_sentences",
    "read_file",
    "sentences_from_file",
]
