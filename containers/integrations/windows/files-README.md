# Windows file and volume metadata

Copy `WinFiles.bui` beside your application and use `Import WinFiles As Files`.
The module provides read-only native Windows operations with explicit UTF-16LE
marshalling and owned UTF-8 output. No helper DLL or extra Buoy package is
required. Deploy the whole compiler output directory with its Buoy runtime DLLs.

| API | Behavior |
| --- | --- |
| `IsSupported()` | True when targeting Windows. Safe on every platform. |
| `ReadFileInfo(filePath)` | Returns a `FileInfo` snapshot; errors preserve the Win32 error code. |
| `Exists(filePath)` | False for missing file/path errors (2 and 3); other failures throw. |
| `ReadDiskSpace(directoryPath)` | Returns caller-available bytes, quota-limited total bytes, and volume-wide free bytes. |
| `FullPath(filePath)` | Returns the absolute lexical path; does not require existence or resolve links. |

`FileInfo` exposes `Attributes`, `IsDirectory`, `IsReadOnly`, `IsHidden`,
`IsReparsePoint`, `SizeBytes`, `CreationFileTime`, `LastAccessFileTime`, and
`LastWriteFileTime`. File size is meaningful for files, not directories.
The timestamp values are unsigned native FILETIME values: 100-nanosecond
intervals since 1601-01-01 UTC. Filesystems may return zero for unsupported
timestamps, use different resolutions, or defer access-time updates.
Reparse-point attributes describe the link itself, not a resolved target.
Use type inference for returned objects, as demonstrated by the smoke program.

`DiskSpace` exposes `AvailableToCallerBytes`, `TotalBytes`, and `TotalFreeBytes`.
Windows disk quotas can restrict the first two. `TotalFreeBytes` is the free
space on the volume and can exceed the caller's quota-limited `TotalBytes`.
Pass an existing directory. UNC share roots require a trailing backslash.
These values are snapshots and may change immediately after querying.

Native operations throw `UnsupportedOperationException` on non-Windows hosts.
Empty or oversized paths throw `InvalidArgumentException`; native failures
throw `RuntimeException` with the Win32 value in `ErrorCode`. Inputs are
validated for zero UTF-8 bytes before conversion. Buoy 0.72.0 currently cannot
construct an embedded NUL with `String.Chr(0)` (it produces an empty string),
so callers must not use that expression to validate input or build NUL tests.

The native metadata structure is nine adjacent DWORD fields (36 bytes,
alignment 4), including split FILETIME values. Pairs are combined into unsigned
64-bit values after the call. The module uses `Optional Declare` against
`kernel32`, avoiding omissions in Buoy's bundled import-library stubs.

Input buffers permit up to 32766 UTF-16 code units plus a terminator. This
capacity does not enable Windows long-path support by itself: normal MAX_PATH,
application-manifest, and extended `\\?\` path rules still apply. No prefix
is added automatically. Relative paths depend on the process current directory;
coordinate changes to it in multithreaded applications. An `Exists` check is
not an access guarantee and must not be used as a replacement for handling
failure when the file is subsequently opened.

## Sources

Feature inspiration: [MBS Win Plugin](https://www.monkeybreadsoftware.de/xojo/plugin-win.shtml)
file-information examples. This is an original Buoy implementation using
Microsoft's native contracts:

- [GetFileAttributesExW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileattributesexw)
- [WIN32_FILE_ATTRIBUTE_DATA](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/ns-fileapi-win32_file_attribute_data)
- [GetDiskFreeSpaceExW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getdiskfreespaceexw)
- [GetFullPathNameW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfullpathnamew)
