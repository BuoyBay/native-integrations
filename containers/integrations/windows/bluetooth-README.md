# Windows Bluetooth radio discovery

Copy `WinBluetooth.bui` into a Buoy 0.72.0 project and import `WinBluetooth`,
optionally with an alias. `bluetooth-smoke.bui` is a complete usage example.

| API | Result |
| --- | --- |
| `IsSupported()` | True for a Windows target. |
| `IsAvailable()` | Whether SetupAPI/kernel32 load; does not imply a radio exists. |
| `PresentRadios()` | `Array Of BluetoothRadio` for local present Bluetooth radio device nodes. |

A `BluetoothRadio` exposes owned `InstanceId` text, optional `Name` and
`Manufacturer`, and the numeric `DeviceNode`. The name prefers the friendly name
and falls back to the device description. Missing properties remain `None`.
Identifiers are PnP identifiers, not Bluetooth MAC addresses; treat them as
opaque. Device-node numbers can become invalid after removal.

The module discovers radios through the documented
`GUID_BTHPORT_DEVICE_INTERFACE` (`0850302A-B344-4FDA-9BE9-90576B8D46F0`) and
`DIGCF_PRESENT | DIGCF_DEVICEINTERFACE`. Drivers register this interface for
local Bluetooth radios. The returned record is the corresponding PnP node.
An absent radio produces an empty array. This API does not discover nearby
peers, enumerate paired devices, expose GATT services, scan, pair, connect,
change radio power, or open hardware handles. It does not require a Bluetooth
radio CPL or a desktop session; the backend is the normal Windows SetupAPI.

All text is copied from bounded UTF-16 native buffers. Information sets are
released with `SetupDiDestroyDeviceInfoList` in `Finally`. A missing native
backend/export raises `LibraryUnavailableException`. Native errors other than
an absent optional property raise `RuntimeException` with the Win32 error in
`ErrorCode`; hotplug can require retrying a fresh enumeration. Library loading,
radio presence, radio enablement and Bluetooth service availability are distinct:
`IsAvailable()` checks only library loading, and records do not claim a radio is
powered on or operational.

The 32-byte `SP_DEVINFO_DATA` record supports x86-64/ARM64 Windows.
`IsSupported()` and `IsAvailable()` return false on other targets;
`PresentRadios()` throws `UnsupportedOperationException` there.

## Native contracts

- [Bluetooth radio interface GUID](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/guid-bthport-device-interface)
- [SetupDiGetClassDevsW](https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdigetclassdevsw)
- [Enumerating device information](https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdienumdeviceinfo)
- [Device instance IDs](https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdigetdeviceinstanceidw)
- [Device properties](https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdigetdeviceregistrypropertyw)
