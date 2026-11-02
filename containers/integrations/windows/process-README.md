# Windows current-process diagnostics

Copy `WinProcess.bui` into a Buoy project and `Import WinProcess As Diagnostics`.
`Diagnostics.IsSupported()` reports whether the target is Windows.
`Diagnostics.ReadCurrentProcess()` returns an owned `ProcessSnapshot` with:

| Property | Meaning |
| --- | --- |
| `CreationFileTime` | Unsigned 100-nanosecond intervals since 1601-01-01 UTC, the native Windows creation timestamp |
| `KernelSeconds`, `UserSeconds` | CPU seconds summed across all process threads |
| `HandleCount` | Number of executive-object handles owned by the process |
| `Memory` | `ProcessMemory` record: working set, peak working set, paged/nonpaged pool, commit and private commit bytes, page faults |
| `IO` | `ProcessIO` record: read/write/other operation and transferred-byte counters |

Use type inference for the snapshot (`Var sample = Diagnostics.ReadCurrentProcess()`)
because Buoy 0.72 has limitations resolving imported types through aliases.
The snapshot samples separate API calls, so fields do not represent one atomic
instant. CPU seconds measure consumption, not wall-clock duration or CPU usage
percentage. IO counters include accounting for files, devices and network IO.
Memory counters follow Windows process accounting; commit is not physical RAM.
The API inspects only its own process and requires no elevation. It opens no real
handles and must not close the `GetCurrentProcess` pseudo-handle.

Targets x86-64 and ARM64 Windows with Buoy 0.72.0. The native APIs are available
since Windows 7; Buoy's own runtime requirements still apply. Sized fields match
`FILETIME` (8 bytes), `IO_COUNTERS` (48 bytes), and
`PROCESS_MEMORY_COUNTERS_EX` (80 bytes on these 64-bit Windows ABIs).
Functions use `Optional Declare` with `kernel32` because upstream SDK import
stubs do not expose every Win32 symbol. Missing exports throw
`LibraryUnavailableException`; native failures throw `RuntimeException` with
`ErrorCode`. Other platforms reject `ReadCurrentProcess()` with
`UnsupportedOperationException` while `IsSupported()` remains available.

## References

Feature inspiration: Monkeybread's [WinFrameworks](https://www.monkeybreadsoftware.de/xojo/plugin-winframeworks.shtml)
process diagnostics and [Win](https://www.monkeybreadsoftware.de/xojo/plugin-win.shtml)
process-statistics examples. This is original Buoy source using Microsoft's
native contracts:

- [GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes)
- [GetProcessHandleCount](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesshandlecount)
- [GetProcessMemoryInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo)
- [PROCESS_MEMORY_COUNTERS_EX](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex)
- [GetProcessIoCounters](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getprocessiocounters)
- [IO_COUNTERS](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-io_counters)
