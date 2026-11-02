# Linux process inspection

Copy `linuxprocess.bui` beside your source and use `Import linuxprocess As Processes`.
The module provides read-only inspection through Linux `/proc` and glibc. It
requires no subprocess, shell, display, privilege escalation, or extra package.
Deploy the full compiler output directory with Buoy's runtime libraries.

| API | Result / behavior |
| --- | --- |
| `IsSupported()` | True for Linux; safe on every platform |
| `ProcessIds()` | Unsorted snapshot of numeric process directories visible in `/proc` |
| `ReadProcess(pid)` | Owned `ProcessInfo` from `/proc/PID/stat`, plus executable-link information |
| `ParseStat(text)` | Parses a stat record into `ProcessInfo`, without reading files |

`ProcessInfo` has `ProcessId`, `Name`, `State`, `ParentProcessId`, `ThreadCount`,
`StartTimeTicks`, `ExecutablePath`, and `ExecutableError`. Use type inference for
returned instances because Buoy 0.72 has limitations resolving class names
through import aliases. `Name` is the kernel's short comm value, not a complete
executable name or command line. `State` preserves the kernel's one-character
state. `StartTimeTicks` counts clock ticks since boot; it is not seconds or a
wall-clock timestamp. It can help detect PID reuse when comparing samples.

The parser finds the final closing parenthesis around comm before splitting
numeric fields. Embedded spaces, parentheses and newlines in a process name
therefore remain intact. Numeric fields are checked for invalid decimal text
and signed-64-bit overflow. The parser reads through stat field 22 and ignores
subsequent fields for compatibility with newer kernels. Invalid/incomplete
records throw `InvalidArgumentException`.

`ReadProcess` requires a PID in 1..2147483647. Failure opening/reading its stat
record throws `RuntimeException` with native `errno` in `ErrorCode`, including
ENOENT when a process disappears or is hidden. Permission errors are preserved.
The independently read executable link is optional: `ExecutablePath.HasValue`
means success; otherwise `ExecutableError` contains readlink's errno. Permission
checks, kernel threads, zombies, and a terminated main thread can make that
link unavailable even when stat is readable. Deleted executable links retain
the kernel's ` (deleted)` suffix. `ParseStat` alone leaves the executable
optional empty with error zero because it does not attempt that operation.

Enumeration is a snapshot, not a promise the listed processes still exist.
`hidepid`, PID namespaces and the mounted proc filesystem constrain visibility.
The separate stat and exe reads are not atomic; a PID can exit and be reused
between them. Do not use this module as an identity or authorization mechanism.
It never reads process environment, signals processes, or opens pidfds.

The module supports x86-64/ARM64 glibc Linux. Its directory reader uses the
64-bit glibc `dirent.d_name` offset of 19 bytes. Native calls use `Optional
Declare Lib "c"` to resolve libc.so.6 without relying on SDK import stubs.
Directory streams, file streams and allocated buffers are released in `Finally`.
Stat records and executable-link text are bounded to 65535 bytes; larger results
throw rather than truncate. Text must be valid UTF-8; non-UTF-8 names/paths fail
conversion. Native NUL cannot be represented by Buoy 0.72 String values.
All operations except `IsSupported()` throw `UnsupportedOperationException`
on non-Linux targets.
