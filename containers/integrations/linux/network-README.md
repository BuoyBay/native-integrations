# Linux interface addresses

Copy `linuxnetwork.bui` beside your Buoy application's source and use
`Import linuxnetwork As Network`. `Network.InterfaceAddresses()` returns an
`Array Of InterfaceAddress` with owned records. `network-smoke.bui` is a complete
example; use type inference (`Var addresses = Network.InterfaceAddresses()`)
when accessing imported class types through an alias in Buoy 0.72.0.

| API | Behavior |
| --- | --- |
| `IsSupported()` | True for Linux targets; safe on other platforms. |
| `InterfaceAddresses()` | IPv4 and IPv6 address records in the calling process's network namespace. |

Each record exposes these properties:

| Property | Type | Meaning |
| --- | --- | --- |
| `Name` | `String` | Interface name, copied and UTF-8 validated. |
| `Family` | `Integer` | Linux `AF_INET` (2) or `AF_INET6` (10). |
| `Address` | `String` | Numeric address produced by `inet_ntop`; no DNS lookup. |
| `Netmask` | `Optional Of String` | Numeric netmask when a matching-family native mask is present. |
| `ScopeId` | `Integer` | IPv6 `sin6_scope_id`, zero for IPv4. |
| `Flags` | `UInt32` | Native interface flags from `getifaddrs`. |
| `IsUp` | `Boolean` | `IFF_UP` flag; does not establish Internet reachability. |
| `IsLoopback` | `Boolean` | `IFF_LOOPBACK` flag. |

There is one record per IP address, so a name may occur multiple times. Native
link-layer records, interfaces without an IPv4/IPv6 address, and NULL address
records are omitted. An empty result is valid. The order and set can change
between calls, including when containers or VPNs change interfaces.

IPv6 `Address` does not include a `%zone` suffix. Preserve `ScopeId` separately
when using scoped addresses; a link-local address may require its interface
index to be usable. The module reports addresses and masks, not routes, default
interfaces, DNS servers, MAC addresses, or connectivity. No interface settings
are changed and no external network traffic is generated.

## Native behavior and limits

Supports Buoy 0.72.0 on 64-bit glibc Linux (x86-64 and ARM64). The native
`ifaddrs` record has size 56 and alignment 8; the wrapper copies it into a
matching `Sequential Structure`. It reads the 16-bit socket family and uses
Linux IPv4/IPv6 address offsets, including the 32-bit IPv6 scope ID. These ABI
assumptions are not portable to other operating systems or 32-bit Linux.

All bindings use `Optional Declare Lib "c"`, which resolves `libc.so.6` without
requiring complete symbols in Buoy's SDK linker stubs. Missing libraries or
symbols throw `LibraryUnavailableException`. Native `getifaddrs` or
`inet_ntop` errors throw `RuntimeException` with Linux `errno` in `ErrorCode`.
An invalid UTF-8 interface name raises `InvalidArgumentException`. Metadata
operations throw `UnsupportedOperationException` on non-Linux targets.

The native linked list is freed in `Finally`, including if conversion fails.
Names and addresses are copied through `CString` conversion before cleanup;
no native pointer escapes the module. Deploy the compiler's complete output
directory, and install GLib/GIO if required by its generated
`libbuoy_system.so` (Debian/Ubuntu: `libglib2.0-0t64`).
