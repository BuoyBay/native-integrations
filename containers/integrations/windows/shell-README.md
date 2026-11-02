# Windows known-folder discovery

Copy `WinShell.bui` beside your Buoy source and use `Import WinShell As FolderInterop`.
The module resolves the current user's registered folder locations through the
Windows shell, including redirected locations. It does not create directories,
launch applications, or change shell settings. No extra Buoy packages or helper
DLLs are needed; deploy the compiler's complete output directory.

| API | Windows known-folder identifier |
| --- | --- |
| `IsSupported()` | Whether the target is Windows; safe on every platform |
| `ProfileDirectory()` | `FOLDERID_Profile` |
| `DocumentsDirectory()` | `FOLDERID_Documents` |
| `DesktopDirectory()` | `FOLDERID_Desktop` |
| `DownloadsDirectory()` | `FOLDERID_Downloads` |
| `LocalAppDataDirectory()` | `FOLDERID_LocalAppData` |
| `RoamingAppDataDirectory()` | `FOLDERID_RoamingAppData` |

Every directory function returns owned UTF-8 text decoded from native UTF-16LE.
The shell supplies the location; the code does not construct paths from English
folder names or environment variables. Redirected folders can be outside the
profile directory, on another volume, or on a UNC share. Folder discovery does
not establish existence, permissions, accessibility, or writability.

The call uses `KF_FLAG_DONT_VERIFY` (0x4000), never `KF_FLAG_CREATE`. This allows
discovery without requiring the directory to exist or contacting its redirected
target to check existence. A user profile and known-folder registration must
still be available; services or incompletely provisioned accounts can fail.
The functions use the current process user's token (`NULL`), not another user's
profile or the interactive console user when running as a service.

Native failures raise `RuntimeException` with the signed 32-bit HRESULT in
`ErrorCode`; these are HRESULTs, not `GetLastError()` values. Missing native
libraries or exports raise `LibraryUnavailableException`. Operations on other
platforms raise `UnsupportedOperationException`; `IsSupported()` remains safe.
Unexpected NULL, empty or over-32767-code-unit output raises `RuntimeException`.
Invalid UTF-16 raises `EncodingException`.

The six GUIDs are 16-byte native representations: the first three GUID fields
use little-endian byte order, while the final eight bytes retain their written
order. The API receives a pointer to the GUID and writes a pointer through
`ByRef Ptr`. `DWORD` is `UInt32` and `HRESULT` is `Int32`; pointers are native
width. This module targets Buoy 0.72.0 x86-64/ARM64 Windows. Its native APIs are
available from Windows Vista; Buoy's runtime platform requirements still apply.
`Optional Declare` avoids requiring missing SDK import stubs.

The native string is copied before `CoTaskMemFree()` runs in `Finally`, including
when conversion fails. The API output is also freed after a failed HRESULT when
non-NULL, as required by Microsoft's contract. No native handle escapes the API.

## References

This original Buoy integration extends the shell-utility feature area suggested
by the [Monkeybread Windows catalog](https://www.monkeybreadsoftware.de/xojo/plugin-win.shtml).
No plugin code or dependency is used. Native contracts and identifiers follow:

- [SHGetKnownFolderPath](https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-shgetknownfolderpath)
- [KNOWNFOLDERID](https://learn.microsoft.com/en-us/windows/win32/shell/knownfolderid)
- [KNOWN_FOLDER_FLAG](https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/ne-shlobj_core-known_folder_flag)
- [CoTaskMemFree](https://learn.microsoft.com/en-us/windows/win32/api/combaseapi/nf-combaseapi-cotaskmemfree)
- [lstrlenW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-lstrlenw)
