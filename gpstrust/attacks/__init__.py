"""Attack simulation at the NMEA data layer.

Real RF spoofing is illegal, so attacks are injected into real captures
instead. The substrate is always genuine receiver output; only the attack is
synthetic.
"""

from .injector import (
    Context,
    InjectionResult,
    Scenario,
    all_scenarios,
    assemble_with_flags,
    combined,
    control,
    decimal_to_nmea,
    hdop_anomaly,
    inject,
    nmea_to_decimal,
    position_drift,
    position_jump,
    satellite_count,
    shift_time_field,
    snr_uniform,
    time_drift,
    time_step,
)

__all__ = [
    "Scenario", "Context", "InjectionResult", "inject", "all_scenarios",
    "assemble_with_flags",
    "control", "position_jump", "position_drift", "time_step", "time_drift",
    "satellite_count", "hdop_anomaly", "snr_uniform", "combined",
    "nmea_to_decimal", "decimal_to_nmea", "shift_time_field",
]
