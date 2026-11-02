# Windows Credential Manager

`WinCredentials.bui` stores application-owned generic credentials in the current
Windows logon session. Copy it beside your entry file and use
`Import WinCredentials As Credentials`. No extra Buoy package is required.

| API | Behavior |
| --- | --- |
| `IsSupported()` | Safe on every platform; true for Windows targets. |
| `ReadGeneric(applicationName, key)` | `Optional Of GenericCredential`; `None` only for a missing entry. |
| `StoreGeneric(applicationName, key, userName, secret, persistAcrossLogons = False)` | Creates or replaces the named generic entry; `secret` is binary `Bytes`. |
| `DeleteGeneric(applicationName, key)` | Deletes that entry; returns false when already absent. |

`GenericCredential` contains `UserName As String`, `Secret As Bytes`, and the native
`Persistence As Integer` (1 session, 2 local-machine, 3 enterprise). Text and bytes are
owned copies and remain valid after the native credential allocation is freed.
The binary secret may contain NUL and arbitrary byte values. Empty secrets are
supported and differ from missing entries. The module never enumerates entries.

Targets are always `Buoy/<applicationName>/<key>`. Application names are nonempty,
limited to 128 UTF-16 code units, and cannot contain `/` or `\`; keys are
nonempty and limited to 1024 UTF-16 code units. Windows target matching is
case-insensitive. Choose a stable company/application identifier and a separate
key for each account. Writes replace only that exact generic target. The wrapper
has no create-only transaction, so coordinate concurrent writers to the same key.

Usernames may be empty and are limited to 513 UTF-16 code units. Secrets are
limited to 2560 bytes. Default persistence is `CRED_PERSIST_SESSION`: entries expire when the logon
session ends. Pass `persistAcrossLogons: True` explicitly to retain that current
user's entry across logons on the local computer (`CRED_PERSIST_LOCAL_MACHINE`).
The wrapper never requests enterprise roaming persistence. This module does not manage browser vaults or third-party password-manager
applications. Returned secrets remain in ordinary mutable Buoy buffers; this
wrapper does not provide a secure-memory or automatic-zeroization guarantee.

`Optional Declare` resolves `advapi32` credential APIs at runtime. Sized fields
match the 80-byte `CREDENTIALW` layout on x86-64 and ARM64 Windows. The returned
native allocation is released with `CredFree` in `Finally`, including failures
while copying the secret. Native failures preserve Win32 `ErrorCode` in a
`RuntimeException`; missing native libraries/exports raise
`LibraryUnavailableException`. Missing credentials use error 1168. A logon session
without a credential set can fail with error 1312, rather than reporting absence.
Other platforms raise `UnsupportedOperationException` for native operations.

Inputs are checked for zero UTF-8 bytes before conversion. Buoy 0.72.0 currently
turns `String.Chr(0)` into an empty string and can truncate decoded strings at NUL;
this module cannot recover data already removed by the language runtime. Secrets
use `Bytes` to avoid that string limitation.
