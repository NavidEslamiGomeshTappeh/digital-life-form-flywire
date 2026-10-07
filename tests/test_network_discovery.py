from __future__ import annotations

import sys
import types

import pytest

from dlf_flywire.network_discovery import (
    DiscoveredONVIFDevice,
    NetworkDiscoveryError,
    build_discovery_receipt,
    discover_onvif_devices,
)


def test_discovery_normalizes_device_results(monkeypatch):
    class FakeDiscovery:
        def __init__(self, timeout, interface):
            assert timeout == 3
            assert interface == "192.168.1.10"

        def discover(self, prefer_https, search):
            assert prefer_https is True
            assert search == "Uho-S2E"
            return [
                {
                    "host": "192.168.1.20",
                    "port": 80,
                    "use_https": False,
                    "epr": "urn:uuid:camera-1",
                    "types": ["tds:Device"],
                    "scopes": ["onvif://www.onvif.org/hardware/Uho-S2E"],
                    "xaddrs": ["http://192.168.1.20/onvif/device_service"],
                    "hostname": "Uho-S2E",
                    "services": ["devicemgmt", "media", "ptz"],
                    "date_time": {"utc": "2026-10-07T10:00:00"},
                }
            ]

    monkeypatch.setitem(
        sys.modules,
        "onvif",
        types.SimpleNamespace(ONVIFDiscovery=FakeDiscovery),
    )

    devices = discover_onvif_devices(
        timeout_s=3,
        interface="192.168.1.10",
        search="Uho-S2E",
        prefer_https=True,
    )

    assert devices == (
        DiscoveredONVIFDevice(
            host="192.168.1.20",
            port=80,
            use_https=False,
            epr="urn:uuid:camera-1",
            types=("tds:Device",),
            scopes=("onvif://www.onvif.org/hardware/Uho-S2E",),
            xaddrs=("http://192.168.1.20/onvif/device_service",),
            hostname="Uho-S2E",
            services=("devicemgmt", "media", "ptz"),
            date_time={"utc": "2026-10-07T10:00:00"},
        ),
    )


def test_discovery_builds_receipt_without_movement():
    device = DiscoveredONVIFDevice(
        host="192.168.1.20",
        port=80,
        use_https=False,
        epr="urn:uuid:camera-1",
        types=("tds:Device",),
        scopes=("onvif://www.onvif.org/hardware/Uho-S2E",),
        xaddrs=("http://192.168.1.20/onvif/device_service",),
        hostname="Uho-S2E",
        services=("devicemgmt", "media", "ptz"),
        date_time={},
    )
    receipt = build_discovery_receipt(
        devices=(device,),
        timeout_s=4,
        interface=None,
        search=None,
    )

    assert receipt["device_count"] == 1
    assert receipt["devices"][0]["host"] == "192.168.1.20"
    assert receipt["movement_commands_issued"] is False
    assert receipt["configuration_changes_issued"] is False


def test_discovery_validates_timeout_before_optional_dependency():
    with pytest.raises(NetworkDiscoveryError, match="positive integer"):
        discover_onvif_devices(timeout_s=0)


def test_discovery_fails_closed_without_runtime(monkeypatch):
    def blocked_import(name, *args, **kwargs):
        if name == "onvif":
            raise ImportError("blocked")
        return __import__(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", blocked_import)

    with pytest.raises(NetworkDiscoveryError, match="onvif-python==0.4.4"):
        discover_onvif_devices()
