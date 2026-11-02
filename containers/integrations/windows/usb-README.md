# Windows USB discovery

Copy `WinUSB.bui` into a Buoy 0.72.0 project and import `WinUSB`, optionally
with an alias. The standalone `usb-smoke.bui` demonstrates use.

| API | Result |
| --- | --- |
| `IsSupported()` | True for a Windows compilation target. |
| `IsAvailable()` | Whether SetupAPI and kernel32 load; does not imply USB hardware exists. |
| `PresentDevices()` | `Array Of USBDevice`, one record per present USB-enumerator PnP device node. |

`USBDevice` contains owned `InstanceId` text, optional `Name` and
`Manufacturer` text, and the numeric `DeviceNode` identifier. The display name
uses the friendly-name property when present, otherwise the device description.
A missing text property is `None`; an explicitly empty property remains
`Some("")`. Treat instance IDs as opaque identifiers. A device-node number is
valid only while that device node exists and can change between snapshots.

Enumeration uses `SetupDiGetClassDevsW` with the `USB` enumerator and
`DIGCF_PRESENT | DIGCF_ALLCLASSES`. This includes USB root hubs and composite
functions and does not promise one record per physical peripheral. USB host
controllers enumerated under PCI are outside this list. Device interfaces,
endpoint descriptors, VID/PID parsing, transfers and hotplug subscriptions are
not provided. Discovery opens no device handles and makes no device changes.

An empty array means no matching present nodes. Missing native libraries or
exports raise `LibraryUnavailableException`; other SetupAPI failures raise
`RuntimeException` with the Win32 error in `ErrorCode`. Device removal during
querying can make discovery fail; callers may retry a fresh snapshot. Optional
property absence (`ERROR_INVALID_DATA`) alone is treated as `None`. All returned
text is decoded from bounded, terminated UTF-16 buffers into owned UTF-8 strings.
Native information sets are destroyed in `Finally`, including on exceptions.

`IsSupported()` and `IsAvailable()` are safe on other targets. Discovery throws
`UnsupportedOperationException` there. The module targets 64-bit x86-64/ARM64
Windows. Its 32-byte `SP_DEVINFO_DATA` layout uses explicit DWORD fields, a
16-byte GUID, and a 64-bit reserved member; it is not a 32-bit Windows binding.

## Native contracts

- [Installed-device enumeration](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/enumerating-installed-devices)
- [SetupDiGetClassDevsW](https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdigetclassdevsw)
- [SP_DEVINFO_DATA](https://learn.microsoft.com/en-us/windows/win32/api/setupapi/ns-setupapi-sp_devinfo_data)
- [Device instance IDs](https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdigetdeviceinstanceidw)
- [Device properties](https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdigetdeviceregistrypropertyw)
