# Linux native integrations

Additional source modules are documented separately:

- [System statistics](system-README.md): RAM, swap, load, process and CPU counts.
- [Content types](content-README.md): MIME recognition, descriptions and icon metadata through GIO.
- [Filesystem metadata](filesystem-README.md): disk capacity, symbolic links and canonical paths.
- [Network interfaces](network-README.md): IPv4/IPv6 addresses, masks, scope and interface flags.
- [Process inspection](processes-README.md): process discovery and snapshots from `/proc`.
- [Desktop events](desktop-README.md): X11 desktop property notifications.
- [Password-manager access](secrets-README.md): application secrets through Secret Service.
- [USB discovery](usb-README.md): USB device metadata from sysfs.
- [Bluetooth adapters](bluetooth-README.md): read-only BlueZ adapter discovery.
- [Printing](printing-README.md): CUPS queues, text jobs and Cairo PDF page drawing, also exposed through the [shared printing API](../printing/README.md).

These additions take feature inspiration from the [Monkeybread Linux plugin catalog](https://www.monkeybreadsoftware.net/pluginpart-linux.shtml).

Copy `linuxnative.bui` beside your application's entry file and use `Import linuxnative As Linux`. The module wraps glibc and XDG paths without shell commands, subprocesses, a display server, or third-party packages. `smoke.bui` demonstrates imports, calls, optional values, and exception handling.

Buoy 0.72.0, glibc Linux, x86-64 and ARM64 are supported. `IsSupported()` exists on every target; the other functions exist only in the `#If TargetLinux` branch. Guard Linux calls in portable applications. There are no macOS implementations here.

The generated `libbuoy_system.so` also requires GLib/GIO. On Debian 13 or Ubuntu 24.04, install `libglib2.0-0t64` when deploying to a minimal system. The compiler image recipe includes this dependency.

| API | Result | Behavior |
| --- | --- | --- |
| `IsSupported()` | `Boolean` | Whether this build targets Linux |
| `ProcessId()` / `ParentProcessId()` | `Integer` | PID and parent PID in the process's PID namespace; parent may be zero |
| `UserId()` / `EffectiveUserId()` / `GroupId()` | `Integer` | Real UID, effective UID, and real GID; zero is valid |
| `EnvironmentValue(name)` | `Optional Of String` | Owned UTF-8 copy; `None` for unset, `Some("")` for explicitly empty |
| `HostName()` | `String` | Kernel hostname in the current UTS namespace |
| `MonotonicNanoseconds()` | `Integer` | `CLOCK_MONOTONIC`, for elapsed durations, excluding suspend |
| `UptimeSeconds()` | `Double` | `CLOCK_BOOTTIME`, including suspend; origin follows the Linux time namespace |
| `HomeDirectory()` | `String` | Absolute `HOME`; raises if unset, empty, or relative |
| `ConfigDirectory()` | `String` | Absolute `XDG_CONFIG_HOME`, otherwise `$HOME/.config` |
| `DataDirectory()` | `String` | Absolute `XDG_DATA_HOME`, otherwise `$HOME/.local/share` |
| `CacheDirectory()` | `String` | Absolute `XDG_CACHE_HOME`, otherwise `$HOME/.cache` |
| `StateDirectory()` | `String` | Absolute `XDG_STATE_HOME`, otherwise `$HOME/.local/state` |
| `RuntimeDirectory()` | `Optional Of String` | Absolute `XDG_RUNTIME_DIR`; `None` if unset, empty, or relative; no fallback |

XDG relative paths are ignored according to the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/). These functions resolve paths; they do not create directories or verify existence, ownership, or permissions. In particular, check runtime-directory ownership and mode before using it for sockets or sensitive files. No password-database lookup is performed when `HOME` is unavailable.

`EnvironmentValue` rejects empty names and names containing `=` with `InvalidArgumentException`. Native text is copied using `CString` UTF-8 validation; non-UTF-8 environment values or hostnames raise `InvalidArgumentException`. Environment reads must not race with environment changes in another thread. These helpers read the ordinary process environment and are intended for ordinary applications, rather than privileged/setuid programs. Clock and hostname system-call failures raise `RuntimeException`; failed dynamic symbol loading raises `LibraryUnavailableException`.

The clock record uses two `Int64` fields, matching the 64-bit Linux ABI; 32-bit targets are unsupported. Monotonic readings have an unspecified origin and should only be subtracted, not interpreted as wall-clock timestamps. See the Linux [clock_gettime](https://man7.org/linux/man-pages/man2/clock_gettime.2.html) and [getenv](https://man7.org/linux/man-pages/man3/getenv.3.html) documentation for native contracts.

All native declarations use `Optional Declare Lib "c"`, which resolves `libc.so.6` at runtime. Buoy's shipped libc link stubs omit several required symbols, even though they exist in the runtime libc. Dynamic resolution allows both native compilation and cross-compilation without modifying the SDK or linking host libraries into cross-target builds.

## Canonical package migration

For new shared applications, use the focused BuoyBay compiler packages:
`keychain` for credentials, `printing` for buffered print jobs, `systeminfo`,
`diskspace` and `filetypes` for snapshots, `processkit` for process inspection,
and `usbkit`, `bluetoothkit`, `networkinfo` and `desktopevents` for discovery.
`filesystemkit` adds lexical `AbsolutePath` and resolved `CanonicalPath`.
Check each package's feature predicates and platform notes; support varies by API.
