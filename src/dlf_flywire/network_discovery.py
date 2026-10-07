from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


class NetworkDiscoveryError(RuntimeError):
    """Raised when ONVIF network discovery cannot complete."""


@dataclass(frozen=True)
class DiscoveredONVIFDevice:
    host: str
    port: int
    use_https: bool
    epr: str
    types: tuple[str, ...]
    scopes: tuple[str, ...]
    xaddrs: tuple[str, ...]
    hostname: str | None
    services: tuple[str, ...]
    date_time: dict[str, str]
    
    def to_dict(self) -> dict[str, object]:
        return {
            "host": self.host,
            "port": self.port,
            "use_https": self.use_https,
            "epr": self.epr,
            "types": list(self.types),
            "scopes": list(self.scopes),
            "xaddrs": list(self.xaddrs),
            "hostname": self.hostname,
            "services": list(self.services),
            "date_time": dict(self.date_time),
        }


def _tuple_strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


def discover_onvif_devices(
    *,
    timeout_s: int = 4,
    interface: str | None = None,
    search: str | None = None,
    prefer_https: bool = False,
) -> tuple[DiscoveredONVIFDevice, ...]:
    if isinstance(timeout_s, bool) or not isinstance(timeout_s, int) or timeout_s <= 0:
        raise NetworkDiscoveryError("discovery timeout must be a positive integer")
    if interface is not None and not isinstance(interface, str):
        raise NetworkDiscoveryError("discovery interface must be a string or null")

    try:
        from onvif import ONVIFDiscovery
    except ImportError as exc:
        raise NetworkDiscoveryError(
            "onvif-python==0.4.4 is required for ONVIF discovery; "
            "install the optional ptz runtime"
        ) from exc

    try:
        discovery = ONVIFDiscovery(timeout=timeout_s, interface=interface)
        raw_devices = discovery.discover(
            prefer_https=prefer_https,
            search=search or None,
        )
    except Exception as exc:
        raise NetworkDiscoveryError(f"ONVIF discovery failed: {exc}") from exc

    devices: list[DiscoveredONVIFDevice] = []
    for item in raw_devices:
        host = item.get("host")
        port = item.get("port")
        if not isinstance(host, str) or not host.strip():
            continue
        if isinstance(port, bool) or not isinstance(port, int) or not (1 <= port <= 65535):
            continue

        devices.append(
            DiscoveredONVIFDevice(
                host=host,
                port=port,
                use_https=bool(item.get("use_https", False)),
                epr=str(item.get("epr") or ""),
                types=_tuple_strings(item.get("types")),
                scopes=_tuple_strings(item.get("scopes")),
                xaddrs=_tuple_strings(item.get("xaddrs")),
                hostname=(
                    str(item["hostname"])
                    if item.get("hostname") is not None
                    else None
                ),
                services=_tuple_strings(item.get("services")),
                date_time={
                    str(key): str(value)
                    for key, value in dict(item.get("date_time") or {}).items()
                },
            )
        )

    return tuple(devices)


def build_discovery_receipt(
    *,
    devices: tuple[DiscoveredONVIFDevice, ...],
    timeout_s: int,
    interface: str | None,
    search: str | None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "observed_success",
        "observed_at_utc": datetime.now(UTC).isoformat(),
        "probe": {
            "protocol": "ONVIF WS-Discovery",
            "timeout_seconds": timeout_s,
            "interface": interface,
            "search": search,
        },
        "device_count": len(devices),
        "devices": [device.to_dict() for device in devices],
        "movement_commands_issued": False,
        "configuration_changes_issued": False,
    }
