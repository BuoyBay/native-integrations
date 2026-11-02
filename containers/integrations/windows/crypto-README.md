# Windows random bytes and SHA-256

Copy `WinCrypto.bui` beside your source and use `Import WinCrypto As Crypto`.
The module wraps Windows CNG in `bcrypt.dll`; it requires no extra Buoy
package, helper DLL, elevated privileges, or application configuration.
Deploy the complete compiler output directory with Buoy's runtime DLLs.

| API | Result |
| --- | --- |
| `IsSupported()` | Whether the compiled target is Windows. Safe on every platform. |
| `RandomBytes(count)` | Owned `Bytes` filled by the Windows system-preferred cryptographic random generator. |
| `Sha256(input)` | Owned 32-byte SHA-256 digest of a `Bytes` instance, including any embedded NUL bytes. |

Both operation sizes are limited to 16 MiB (16777216 bytes) per call.
`RandomBytes(0)` returns an empty buffer without a native call. Negative
or oversized counts, oversized hash inputs, and `Nil` hash inputs raise
`InvalidArgumentException`. An empty `Bytes` is a valid hash input.
`Sha256` leaves its input unchanged. Callers should not mutate an input
buffer concurrently with hashing.

The SHA-256 wrapper uses the `BCryptHash` convenience API, requiring
Windows 10 or Windows Server 2016 or later. Targets are 64-bit x86-64 and
ARM64 Windows with Buoy 0.72.0. Buoy's own runtime requirements also apply.
`IsSupported()` checks the compilation target, not the Windows version
or native symbol availability. Native operations on another platform
raise `UnsupportedOperationException`.

All declarations are `Optional Declare` against `bcrypt`, avoiding
dependence on the SDK's import-library coverage. Missing libraries or
exports raise `LibraryUnavailableException`. A failing native operation
raises `RuntimeException` with the signed 32-bit NTSTATUS in `ErrorCode`
and the operation name in the message. NTSTATUS values are checked by
their sign and must not be interpreted as Win32 `GetLastError` codes.

`RandomBytes` passes a null algorithm handle with the system-preferred RNG
flag. `Sha256` opens the default SHA-256 provider for each call and closes
its handle in `Finally`, including when hashing fails. No native handle
escapes the module. Native buffer sizes are 32-bit unsigned values;
handles and buffer addresses use `Ptr` on both supported Windows ABIs.
The returned digest can be encoded with the standard `Bytes.ToHex()`.

## Native references

These original Buoy bindings follow Microsoft's API contracts:

- [BCryptGenRandom](https://learn.microsoft.com/en-us/windows/win32/api/bcrypt/nf-bcrypt-bcryptgenrandom)
- [BCryptHash](https://learn.microsoft.com/en-us/windows/win32/api/bcrypt/nf-bcrypt-bcrypthash)
- [BCryptOpenAlgorithmProvider](https://learn.microsoft.com/en-us/windows/win32/api/bcrypt/nf-bcrypt-bcryptopenalgorithmprovider)
- [BCryptCloseAlgorithmProvider](https://learn.microsoft.com/en-us/windows/win32/api/bcrypt/nf-bcrypt-bcryptclosealgorithmprovider)
