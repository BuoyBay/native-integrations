# Linux Bluetooth adapter discovery

Copy `linuxbluetooth.bui` beside your source and
`Import linuxbluetooth As BluetoothInterop`.
`Adapters()` queries existing BlueZ adapters over system D-Bus and returns
owned `BluetoothAdapter` records. It never scans, pairs, connects, changes power,
starts a daemon, or writes properties. The call uses `NO_AUTO_START` and a
five-second method timeout.

| Property | Meaning |
| --- | --- |
| `ObjectPath` | BlueZ adapter object path, such as `/org/bluez/hci0` |
| `Address` | Adapter Bluetooth address reported by BlueZ |
| `Name`, `Alias` | Optional adapter names, copied as UTF-8 |
| `Powered`, `Discovering`, `Discoverable` | Optional Boolean state properties |

`IsSupported()` detects Linux. `IsAvailable()` tests GLib/GObject/GIO library
loading only: it does not claim that BlueZ or the system bus is running.
A failed bus connection, absent BlueZ owner, denied query, malformed reply, or
other backend failure throws `RuntimeException` with the native GError code in
`ErrorCode` and explanatory text. An empty array means a successful query with
zero adapter objects. Those are distinct outcomes. No discovery results or
nearby devices are returned; querying does not expose pairing keys.

`DecodeManagedObjects(text)` accepts a recorded ObjectManager reply in GLib's
GVariant text notation, requiring the exact `(a{oa{sa{sv}}})` signature. It is
useful for offline snapshots and deterministic tests. For example,
`(@a{oa{sa{sv}}} {},)` is a successful empty snapshot. Adapter properties are
validated by type; non-adapter objects are ignored. All returned data is copied
before variants are freed. Every owned GVariant, GError, and GObject is released
in `Finally` or at its error boundary.

Dependencies are GLib/GIO >= 2.30, a system D-Bus, and BlueZ implementing
`org.bluez.Adapter1`. Debian/Ubuntu runtime libraries come from
`libglib2.0-0t64` (or `libglib2.0-0` on older releases); BlueZ is a separate
system service. Libraries use versioned `Optional Declare` names, without
requiring development packages. Missing libraries/exports raise
`LibraryUnavailableException`. Non-Linux metadata operations throw
`UnsupportedOperationException`. The native GError layout is the 16-byte
LP64 layout, so x86-64 and ARM64 Linux are supported.

The query is synchronous and is a snapshot. Adapter power/state may change
immediately afterwards. Optional properties preserve absence; they are not
silently replaced by false or empty strings.
