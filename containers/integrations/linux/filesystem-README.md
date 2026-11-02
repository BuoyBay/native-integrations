# Linux filesystem metadata

Copy `linuxfilesystem.bui` beside your application's source and import
`linuxfilesystem`, optionally aliased as `Files`. The module supports Buoy
0.72.0 on 64-bit glibc Linux, x86-64 and ARM64. It needs no extra Buoy package
or subprocess. Deploy the complete compiler output directory as usual.

| API | Result and behavior |
| --- | --- |
| `IsSupported()` | Whether this target is Linux; safe on every platform. |
| `ReadSpace(filePath)` | `FileSystemSpace` for the filesystem containing an existing path; follows symbolic links. |
| `ReadSymbolicLink(filePath)` | Owned UTF-8 text stored in a symbolic link, preserving relative targets and dangling links. |
| `CanonicalPath(filePath)` | Absolute path with links, `.` and `..` resolved; the target must exist. |

Use type inference for the returned `FileSystemSpace` object, as demonstrated
by `filesystem-smoke.bui`. Its properties preserve native values:

- `BlockSizeBytes`, `FragmentSizeBytes`: preferred filesystem block size and
  the fragment size used for capacity calculations.
- `TotalBlocks`, `FreeBlocks`, `AvailableBlocks`: counts in fragment units;
  available blocks apply to unprivileged users and can exclude reserved space.
- `TotalBytes`, `FreeBytes`, `AvailableBytes`: respective counters multiplied
  by `FragmentSizeBytes`, using unsigned 64-bit arithmetic.
- `TotalInodes`, `FreeInodes`, `AvailableInodes`: native inode counters.
- `FileSystemId`, `MountFlags`, `MaximumNameBytes`: filesystem identifier,
  native mount flags, and filename-component byte limit.

Filesystem statistics are snapshots. Some filesystems do not provide meaningful
values for every field. They describe a mount, and do not establish that a
specific future write will succeed. Byte products assume they fit in `UInt64`.
Raw counters and units are retained for callers needing native interpretation.

`ReadSymbolicLink` reads only the final link's stored target. It grows its
buffer when `readlink` reports a full buffer, up to a 1 MiB limit, and throws
instead of returning potentially truncated text. Link replacement can race
with reads. `CanonicalPath` performs resolution at the time of the call; it
does not keep a handle open or guarantee subsequent access to the same object.
Neither helper is an authorization check.

## Errors and native ABI

Native failures throw `RuntimeException`, with Linux `errno` preserved in
`ErrorCode`. Missing libraries or exports throw `LibraryUnavailableException`.
All operations except `IsSupported()` throw `UnsupportedOperationException`
on other platforms. Empty paths and NUL bytes present in UTF-8 input are
rejected with `InvalidArgumentException`.

Paths and returned targets use UTF-8. Linux filenames can contain non-UTF-8
bytes, which these String APIs cannot represent; invalid returned UTF-8 throws
an encoding/conversion exception. Buoy 0.72.0 currently turns `String.Chr(0)`
into an empty string and can truncate decoded NUL, so validation cannot recover
data already lost by the language runtime.

The native `statvfs` record is 112 bytes with 8-byte alignment on the supported
glibc LP64 targets. The binding preserves the trailing reserved storage and
uses sized integers. All declarations use `Optional Declare Lib "c"`, resolving
`libc.so.6` at runtime. `realpath`'s allocated result is copied before being
freed in `Finally`. Readlink buffers are managed Buoy `Bytes` objects.
