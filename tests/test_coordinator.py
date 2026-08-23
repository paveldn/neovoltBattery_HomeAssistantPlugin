"""Tests for coordinator data stabilization helpers."""
from __future__ import annotations

import pytest

pytest.importorskip("homeassistant")
pytest.importorskip("voluptuous")

from custom_components.bytewatt.coordinator import ByteWattDataUpdateCoordinator


class _Diagnostics:
    def __init__(self):
        self.entries = []

    def log_diagnostic(self, event, details):
        self.entries.append((event, details))


def _coordinator_with_last_data(last_data):
    coordinator = object.__new__(ByteWattDataUpdateCoordinator)
    coordinator._last_battery_data = last_data
    coordinator.diagnostic_service = _Diagnostics()
    return coordinator


def test_stabilize_cumulative_energy_keeps_previous_on_drop():
    coordinator = _coordinator_with_last_data({
        "Total_Battery_Charge": 14.9,
        "soc": 80,
    })

    result = coordinator._stabilize_cumulative_energy({
        "Total_Battery_Charge": 6.8,
        "soc": 75,
    })

    assert result["Total_Battery_Charge"] == 14.9
    assert result["soc"] == 75
    assert coordinator.diagnostic_service.entries == [
        (
            "energy_total_stabilized",
            {
                "key": "Total_Battery_Charge",
                "reported_value": 6.8,
                "kept_value": 14.9,
            },
        )
    ]


def test_stabilize_cumulative_energy_keeps_previous_when_missing():
    coordinator = _coordinator_with_last_data({"Total_Battery_Charge": "14.9"})

    result = coordinator._stabilize_cumulative_energy({"soc": 75})

    assert result["Total_Battery_Charge"] == "14.9"


def test_stabilize_cumulative_energy_allows_increase():
    coordinator = _coordinator_with_last_data({"Total_Battery_Charge": 14.9})

    result = coordinator._stabilize_cumulative_energy({
        "Total_Battery_Charge": 15.1,
    })

    assert result["Total_Battery_Charge"] == 15.1
