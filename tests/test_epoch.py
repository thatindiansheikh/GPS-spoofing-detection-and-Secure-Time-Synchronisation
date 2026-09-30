"""Assembly of sentence bursts into per-second epochs."""

from __future__ import annotations

from datetime import datetime, timezone

from gpstrust.nmea import ParseStats, epochs_from_sentences

from conftest import CLEAN_CYCLE, nmea


def _cycle_at(time_str: str, lat: str = "4807.0380", lon: str = "01131.0000", speed: str = "0.06"):
    """A full fix cycle at a given hhmmss.ss, for multi-epoch tests."""
    return [
        nmea(f"GPGGA,{time_str},{lat},N,{lon},E,1,08,0.9,545.4,M,46.9,M,,"),
        nmea("GPGSA,A,3,04,05,09,12,24,,,,,,,,2.5,0.9,2.1"),
        nmea("GPGSV,2,1,08,01,40,083,46,02,17,308,41,12,07,344,39,14,22,228,45"),
        nmea("GPGSV,2,2,08,15,60,058,43,17,10,148,38,18,82,113,47,20,25,033,40"),
        nmea(f"GPRMC,{time_str},A,{lat},N,{lon},E,{speed},84.4,230394,3.1,W"),
    ]


def test_clean_cycle_becomes_one_epoch():
    epochs = list(epochs_from_sentences(CLEAN_CYCLE))
    assert len(epochs) == 1
    ep = epochs[0]
    assert ep.fix_quality == 1
    assert ep.num_sats_used == 8
    assert ep.hdop == 0.9
    assert ep.pdop == 2.5
    assert ep.vdop == 2.1
    assert ep.has_fix


def test_position_is_decoded_to_decimal_degrees():
    ep = list(epochs_from_sentences(CLEAN_CYCLE))[0]
    assert abs(ep.lat - 48.1173) < 1e-4
    assert abs(ep.lon - 11.5166) < 1e-3


def test_gsv_group_accumulates_across_sentences():
    ep = list(epochs_from_sentences(CLEAN_CYCLE))[0]
    assert ep.sats_in_view == 8
    # Two GSV sentences carrying four satellites each.
    assert len(ep.prn) == 8
    assert len(ep.snr) == 8
    assert ep.snr[0] == 46


def test_timestamp_change_closes_the_epoch():
    sentences = _cycle_at("123519.00") + _cycle_at("123520.00")
    epochs = list(epochs_from_sentences(sentences))
    assert len(epochs) == 2
    assert epochs[0].time_key != epochs[1].time_key


def test_utc_is_built_from_rmc_date_and_time():
    ep = list(epochs_from_sentences(CLEAN_CYCLE))[0]
    assert ep.utc == datetime(1994, 3, 23, 12, 35, 19, tzinfo=timezone.utc)


def test_speed_converted_to_metres_per_second():
    ep = list(epochs_from_sentences(CLEAN_CYCLE))[0]
    assert ep.sog_knots == 0.06
    assert abs(ep.sog_mps - 0.06 * 0.514444) < 1e-9


def test_no_fix_is_not_treated_as_a_position():
    sentences = [
        nmea("GPGGA,123519.00,,,,,0,00,,,M,,M,,"),
        nmea("GPRMC,123519.00,V,,,,,,,230394,,"),
        nmea("GPGGA,123520.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,"),
    ]
    epochs = list(epochs_from_sentences(sentences))
    assert epochs[0].has_fix is False
    assert epochs[0].fix_quality == 0
    assert epochs[0].rmc_valid is False


def test_rmc_void_status_invalidates_epoch_with_coordinates():
    # A receiver can report stale coordinates with status 'V'; that must not
    # be accepted as a fix.
    sentences = [
        nmea("GPGGA,123519.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,"),
        nmea("GPRMC,123519.00,V,4807.0380,N,01131.0000,E,0.0,0.0,230394,3.1,W"),
        nmea("GPGGA,123520.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,"),
    ]
    epochs = list(epochs_from_sentences(sentences))
    assert epochs[0].has_position is True
    assert epochs[0].has_fix is False


def test_untracked_satellites_are_excluded_from_snr():
    # Satellites 3 and 4 are in view but have empty SNR fields.
    sentences = [
        nmea("GPGGA,123519.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,"),
        nmea("GPGSV,1,1,04,01,40,083,46,02,17,308,41,12,07,344,,14,22,228,"),
        nmea("GPGGA,123520.00,4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,"),
    ]
    ep = list(epochs_from_sentences(sentences))[0]
    assert len(ep.prn) == 4
    assert len(ep.snr) == 2
    assert ep.snr == [46, 41]


def test_corrupt_lines_inside_a_cycle_do_not_break_assembly():
    stats = ParseStats()
    sentences = list(CLEAN_CYCLE)
    sentences.insert(2, "$GPGSV,2,1,08,01,40,08")          # truncated
    sentences.insert(4, "\xff\xfe\x00 noise")                # binary garbage
    epochs = list(epochs_from_sentences(sentences, stats))
    assert len(epochs) == 1
    assert epochs[0].has_fix
    assert stats.bad >= 1


def test_stream_ending_mid_cycle_still_emits_the_partial_epoch():
    epochs = list(epochs_from_sentences(_cycle_at("123519.00")[:2]))
    assert len(epochs) == 1
    assert epochs[0].has_position


def test_log_starting_mid_cycle_does_not_lose_the_next_one():
    # First line is a fragment with no start delimiter at all.
    sentences = ["0380,N,01131.0000,E,1,08,0.9"] + _cycle_at("123519.00")
    epochs = list(epochs_from_sentences(sentences))
    assert len(epochs) == 1
    assert epochs[0].has_fix
