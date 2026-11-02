# Linux USB discovery

Copy `linuxusb.bui` beside your source and `Import linuxusb As UsbInterop`.
`IsSupported()` is portable. `Devices()` returns owned `UsbDevice` records from
`/sys/bus/usb/devices`, including USB root hubs and excluding interface entries.
No device is opened and no configuration, permission, or driver is changed.

| Property | Meaning |
| --- | --- |
| `SysfsName`, `SysfsPath` | Kernel USB bus entry and the queried path |
| `VendorId`, `ProductId` | Numeric 16-bit USB vendor/product identifiers |
| `BusNumber`, `DeviceNumber` | Kernel bus and device numbers |
| `DevicePath` | Optional port topology string from `devpath` |
| `Manufacturer`, `Product`, `SerialNumber` | Optional owned UTF-8 descriptor strings |

`Devices(sysfsRoot)` accepts an absolute mounted sysfs USB bus tree, also useful
for isolated fixtures. The default always reads the real Linux sysfs path.
A missing or unreadable bus directory throws `RuntimeException`, preserving
`errno` in `ErrorCode`; it is never reported as an empty successful result.
A readable tree with no eligible devices returns an empty array. Missing
required attributes skip a disappearing device; optional absent attributes
remain `None`. Permission and other read failures throw. Enumeration is an
unsorted, non-atomic snapshot: unplug and replug can change IDs or paths during
and after a query. Device numbers and sysfs paths are not persistent identities.
Serial numbers may be absent or duplicated; device-supplied strings are untrusted.

The module reads sysfs attributes as streams rather than trusting their reported
file sizes. It bounds each read to 4095 bytes, preserves UTF-8 through a validated
owned copy, and removes only a final sysfs newline. Numeric IDs and counts are
validated. Invalid UTF-8 cannot be represented by this interface. Paths containing
NUL are rejected if the bytes reach the module; Buoy 0.72 truncates embedded NUL
strings before the module can recover them.

Requires 64-bit glibc Linux (x86-64 or ARM64). Native libc calls use
`Optional Declare Lib "c"` and the LP64 Linux `dirent` name offset 19.
Libraries or symbols missing at runtime raise `LibraryUnavailableException`.
Non-Linux `Devices` calls throw `UnsupportedOperationException`.
