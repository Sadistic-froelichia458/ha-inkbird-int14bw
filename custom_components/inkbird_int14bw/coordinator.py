"""Connection coordinator for the Inkbird INT-14-BW.

Uses Home Assistant's built-in Bluetooth stack (``homeassistant.components
.bluetooth``) plus ``bleak-retry-connector``. This means the same code path
works whether the adapter is a local USB/onboard controller or a remote
ESPHome Bluetooth proxy — HA routes the connection through whichever path can
reach the device, and we never talk to BlueZ directly or fight the scanner
for the adapter.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak_retry_connector import establish_connection

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback

from .auth import (
    build_challenge_request,
    build_clock_sync,
    build_verify_response,
    parse_probe_temp,
)
from .const import (
    CHR_BATTERY,
    CHR_FF01,
    CHR_FF02,
    NUM_PROBES,
)

_LOGGER = logging.getLogger(__name__)

# Probe internal-temperature byte offsets within the FF01 notification,
# confirmed live against known temperatures (see auth.parse_probe_temp).
_PROBE_OFFSETS = (0, 4, 8, 12)

# How long we tolerate no notifications before treating the link as dead.
_STALL_TIMEOUT = 90


class InkbirdData:
    """Latest decoded values from the device."""

    def __init__(self) -> None:
        self.probes: list[float | None] = [None] * NUM_PROBES
        self.battery: int | None = None


class InkbirdCoordinator:
    """Maintains a persistent authenticated BLE session and pushes updates."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        self.hass = hass
        self.address = address.upper()
        self.data = InkbirdData()
        self._client: BleakClient | None = None
        self._listeners: list[Callable[[], None]] = []
        self._run_task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._authed = asyncio.Event()
        self._challenge: bytes | None = None
        self._challenge_evt = asyncio.Event()
        self._last_rx = 0.0
        self._available = False

    # ---- public API -------------------------------------------------------

    @property
    def available(self) -> bool:
        return self._available

    @callback
    def async_add_listener(self, update_callback: Callable[[], None]) -> Callable[[], None]:
        """Register an entity update callback; returns an unsubscribe."""
        self._listeners.append(update_callback)

        def _remove() -> None:
            self._listeners.remove(update_callback)

        return _remove

    @callback
    def _notify_listeners(self) -> None:
        for update_callback in list(self._listeners):
            update_callback()

    async def async_start(self) -> None:
        self._stop.clear()
        self._run_task = self.hass.async_create_task(self._run())

    async def async_stop(self) -> None:
        self._stop.set()
        if self._run_task:
            self._run_task.cancel()
            with contextlib.suppress(Exception):
                await self._run_task
        if self._client and self._client.is_connected:
            await self._client.disconnect()

    # ---- connection loop --------------------------------------------------

    async def _run(self) -> None:
        while not self._stop.is_set():
            device = bluetooth.async_ble_device_from_address(
                self.hass, self.address, connectable=True
            )
            if device is None:
                # Not in range of any adapter/proxy right now — the HA
                # Bluetooth stack will keep scanning; just wait and retry.
                self._set_available(False)
                await self._sleep(20)
                continue

            try:
                await self._session(device)
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001 - resilience loop
                _LOGGER.debug("Inkbird session ended: %s", err)
            self._set_available(False)
            await self._sleep(10)

    async def _session(self, device: BLEDevice) -> None:
        self._authed.clear()
        self._challenge_evt.clear()
        self._challenge = None

        client = await establish_connection(
            BleakClient, device, self.address, max_attempts=4
        )
        self._client = client
        _LOGGER.debug("Connected to %s", self.address)

        try:
            await client.start_notify(CHR_FF02, self._on_ff02)
            await client.start_notify(CHR_FF01, self._on_ff01)
            try:
                await client.start_notify(CHR_BATTERY, self._on_battery)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Battery subscribe failed: %s", err)

            await asyncio.sleep(0.3)
            await client.write_gatt_char(CHR_FF02, build_challenge_request(), response=False)

            try:
                await asyncio.wait_for(self._challenge_evt.wait(), timeout=8)
            except TimeoutError as err:
                raise RuntimeError("no auth challenge received") from err

            assert self._challenge is not None
            await client.write_gatt_char(
                CHR_FF02, build_verify_response(self._challenge), response=False
            )
            try:
                await asyncio.wait_for(self._authed.wait(), timeout=5)
            except TimeoutError:
                _LOGGER.debug("Auth ACK not seen; continuing")

            await asyncio.sleep(0.2)
            await client.write_gatt_char(CHR_FF02, build_clock_sync(), response=False)
            await asyncio.sleep(0.2)
            # Request current temperature / state / battery.
            await client.write_gatt_char(
                CHR_FF02,
                bytes([0x02, 0xF1, 0x01, 0x02, 0xF1, 0x03, 0x02, 0xF1, 0x19]),
                response=False,
            )

            self._set_available(True)
            self._last_rx = self.hass.loop.time()

            # Hold the link open; drop out if it dies or stalls.
            while not self._stop.is_set() and client.is_connected:
                await asyncio.sleep(5)
                if self.hass.loop.time() - self._last_rx > _STALL_TIMEOUT:
                    _LOGGER.debug("Inkbird link stalled, reconnecting")
                    break
        finally:
            self._client = None
            with contextlib.suppress(Exception):
                if client.is_connected:
                    await client.disconnect()

    # ---- notification handlers -------------------------------------------

    @callback
    def _on_ff01(self, _char: BleakGATTCharacteristic, data: bytearray) -> None:
        self._last_rx = self.hass.loop.time()
        changed = False
        for i, off in enumerate(_PROBE_OFFSETS):
            value = parse_probe_temp(bytes(data), off)
            if value != self.data.probes[i]:
                self.data.probes[i] = value
                changed = True
        if changed:
            self._notify_listeners()

    @callback
    def _on_ff02(self, _char: BleakGATTCharacteristic, data: bytearray) -> None:
        self._last_rx = self.hass.loop.time()
        i = 0
        while i + 1 < len(data):
            flen = data[i]
            if flen < 1 or i + 1 + flen > len(data):
                break
            frame_type = data[i + 1]
            payload = data[i + 2 : i + 1 + flen]
            if frame_type == 0xFB and len(payload) == 6:
                self._challenge = bytes(payload)
                self._challenge_evt.set()
            elif frame_type == 0xFC and payload and payload[0] == 0x00:
                self._authed.set()
            i += 1 + flen

    @callback
    def _on_battery(self, _char: BleakGATTCharacteristic, data: bytearray) -> None:
        self._last_rx = self.hass.loop.time()
        if data and data[0] != 0x7F:
            value = min(data[0], 100)
            if value != self.data.battery:
                self.data.battery = value
                self._notify_listeners()

    # ---- helpers ----------------------------------------------------------

    @callback
    def _set_available(self, available: bool) -> None:
        if available != self._available:
            self._available = available
            self._notify_listeners()

    async def _sleep(self, seconds: float) -> None:
        try:
            await asyncio.wait_for(self._stop.wait(), timeout=seconds)
        except TimeoutError:
            pass
