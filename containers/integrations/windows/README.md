# Windows native integrations

Additional reusable modules:

- [Current-process diagnostics](process-README.md): CPU time, memory, handles and IO counters.
- [Files and volumes](files-README.md): native Windows file and storage utilities.
- [Registry values](registry-README.md): Unicode values in the current user's Registry.
- [Cryptography](crypto-README.md): native random bytes and SHA-256 digests.
- [Known folders](shell-README.md): Windows-managed user folder locations.
- [Desktop events](desktop-README.md): native Windows accessibility event notifications.
- [Credential Manager](credentials-README.md): application-scoped generic credentials.
- [USB discovery](usb-README.md): present USB device metadata.
- [Bluetooth adapters](bluetooth-README.md): present Bluetooth radio metadata.
- [Printing](printing-README.md): native printer discovery and GDI page drawing, also exposed through the [shared printing API](../printing/README.md).

These additions take feature inspiration from Monkeybread's
[WinFrameworks](https://www.monkeybreadsoftware.de/xojo/plugin-winframeworks.shtml)
and [Win](https://www.monkeybreadsoftware.de/xojo/plugin-win.shtml) catalogs.

Copy `WinSystem.bui` beside your application's source and import `WinSystem`
(or alias it as `Win`, as `smoke.bui` does). No packages, helper DLLs,
PowerShell, registry changes, or elevated privileges are required. Deploy
the full compiler output directory, including Buoy's runtime DLLs.

| API | Result / behavior |
| --- | --- |
| `IsSupported()` | Whether the compiled target is Windows. |
| `ProcessId()` | Current process ID, widened from Win32 `DWORD` to Buoy `Integer`. |
| `UptimeMilliseconds()` | Unsigned 64-bit milliseconds since system startup, including sleep. This is not a wall clock. |
| `PerformanceTicks()` | High resolution monotonic counter for measuring intervals. |
| `PerformanceFrequency()` | Counter ticks per second. Convert a tick difference to `Double` before dividing to avoid integer truncation. |
| `ReadMemoryStatus()` | Snapshot of physical memory, process commit limits, and virtual address space. |
| `SystemDirectory()` | Windows system directory as owned UTF-8 text. |
| `TemporaryDirectory()` | The process's temporary directory, with a trailing backslash. |
| `EnvironmentValue(name)` | `Optional Of String`: absent differs from present with an empty value. |
| `SetEnvironmentValue(name, value)` | Sets an environment value for this process and future children. |
| `RemoveEnvironmentValue(name)` | Removes an environment value from this process. |

`MemoryStatus` follows the 64-byte `MEMORYSTATUSEX` layout. Its fields are
`Size`, `LoadPercent`, `TotalPhysicalBytes`, `AvailablePhysicalBytes`,
`CommitLimitBytes`, `AvailableCommitBytes`, `TotalVirtualBytes`,
`AvailableVirtualBytes`, and `Reserved`. Memory sizes are unsigned 64-bit
byte counts; the final field is reserved by Windows. Use type inference
for this returned structure, as the compiler does not resolve a qualified
type name through an import alias (see `smoke.bui`).

All native operations throw `UnsupportedOperationException` on other
targets; importing the module and calling `IsSupported()` remains safe.
Native failures throw `RuntimeException` with the Win32 error in
`ErrorCode`. Invalid names, embedded NUL, and oversized environment values
throw `InvalidArgumentException`. Invalid UTF-16 from Windows throws
`EncodingException`. Empty environment names and names containing `=` are
rejected, including Windows' private drive-current-directory entries.

The wide-character APIs explicitly marshal UTF-16LE with a NUL terminator
and decode into owned UTF-8 strings. Non-ASCII and supplementary-plane
characters are preserved. Buffers have 32768 UTF-16 code units; output
which exceeds that capacity fails rather than silently truncating.
Environment operations affect the Windows process environment, not the
C runtime's separately cached environment or the parent shell. Callers
should coordinate concurrent mutation of the same variable.

`TemporaryDirectory()` uses `GetTempPathW` for compatibility with older
Windows versions. The result follows the process environment and does
not guarantee that the directory exists or is writable. Services that
require newer `GetTempPath2W` semantics should implement that policy
explicitly. `SystemDirectory()` is for discovery, not application data.

## References

The copy-and-import approach and native Windows utility idea were inspired
by [WinAPILib](https://github.com/paullefebvre/winapilib). This is an original
Buoy implementation, not a translation of its Xojo declarations.

Signatures and semantics follow Microsoft's documentation for
[process IDs](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getcurrentprocessid),
[uptime](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-gettickcount64),
[performance counters](https://learn.microsoft.com/en-us/windows/win32/api/profileapi/nf-profileapi-queryperformancecounter),
[MEMORYSTATUSEX](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/ns-sysinfoapi-memorystatusex),
[system directories](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getsystemdirectoryw),
[temporary directories](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-gettemppathw),
[reading environment variables](https://learn.microsoft.com/en-us/windows/win32/api/processenv/nf-processenv-getenvironmentvariablew),
and [setting environment variables](https://learn.microsoft.com/en-us/windows/win32/api/processenv/nf-processenv-setenvironmentvariablew).

Buoy 0.72.0 currently drops NUL produced by `String.Chr(0)` and truncates
UTF-8 byte decoding at NUL. Input validation scans the actual UTF-8 bytes
for zero; it cannot recover characters already discarded by the runtime.
The smoke therefore uses a representable invalid environment name.

## Canonical package migration

For new shared applications, use the focused BuoyBay compiler packages:
`keychain` for credentials, `printing` for buffered print jobs, `systeminfo`,
`diskspace` and `filetypes` for snapshots, `processkit` for process inspection,
and `usbkit`, `bluetoothkit`, `networkinfo` and `desktopevents` for discovery.
`filesystemkit` adds lexical `AbsolutePath` and resolved `CanonicalPath`.
Check each package's feature predicates and platform notes; support varies by API.
