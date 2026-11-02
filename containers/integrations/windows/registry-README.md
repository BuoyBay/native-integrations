# Windows Registry string settings

Copy `WinRegistry.bui` beside your entry file and use `Import WinRegistry As Registry`.
This module operates on the current user's **64-bit HKCU registry view**. It
stores Unicode `REG_SZ` application settings without administrator privileges,
helper DLLs, or additional Buoy packages. Deploy the complete compiler output
directory with Buoy's runtime DLLs.

| API | Result / behavior |
| --- | --- |
| `IsSupported()` | Whether the compiled target is Windows; safe everywhere. |
| `CreateKey(keyPath)` | Creates or opens a nonvolatile key; `True` only if newly created. |
| `ReadString(keyPath, name)` | Owned `Optional Of String`; `None` for a missing key or value, `Some("")` for an empty string. |
| `WriteString(keyPath, name, value)` | Writes `REG_SZ` to an existing key. |
| `DeleteValue(keyPath, name)` | Deletes one value; `False` if the key/value is missing. |
| `DeleteLeafKey(keyPath)` | Deletes one key and its values; fails if it has child keys. Missing returns `False`. |

Paths are relative to HKCU, such as `Software\MyCompany\MyApp`. Empty path
components are rejected. Mutations require `Software\<application>\<subkey>`
or deeper; root, `Software`, and an application's top-level key cannot be
modified through these mutation helpers. `CreateKey` may create intermediate
keys. Key and value names follow Windows' case-insensitive registry rules.
An empty value name selects the unnamed/default value.

Reads accept **only `REG_SZ`**, with expansion disabled. `REG_EXPAND_SZ`,
multi-string, numeric and binary values raise a native type error rather than
being converted. String values are limited to 1 MiB including their UTF-16
terminator. A missing key or value is distinguished from access denial and
other failures. The latter throw `RuntimeException` with the API's returned
Win32 status in `ErrorCode`; registry functions return error codes directly,
so `GetLastError()` is not consulted.

Every opened/created key handle is closed in `Finally`, and none escapes the
module. All native APIs use `Optional Declare Lib "advapi32"`; an unavailable
library/export raises `LibraryUnavailableException`. Non-Windows operations
raise `UnsupportedOperationException` before calling native functions.

The two-phase read retries size changes up to four times, then raises. It is
not a transaction. Applications should coordinate concurrent edits to the
same settings. Native UTF-16 output is checked for alignment, termination and
embedded NUL before decoding to an owned UTF-8 string. Invalid UTF-16 raises
`EncodingException`. Buoy 0.72 currently converts `String.Chr(0)` to an empty
string and truncates some decoded strings at NUL; input validation cannot
recover bytes already discarded by that runtime behavior.

`DeleteLeafKey` is deliberately nonrecursive. It removes all values in that
one leaf, including the default value. Use it only for a key your application
owns; it does not promise the key is empty and does not inspect its values.
Writes are persistent registry changes; this module does not flush the
system registry cache explicitly.

## Native references

This is original Buoy code, with feature inspiration from the registry helpers
in the [Monkeybread Win catalog](https://www.monkeybreadsoftware.de/xojo/plugin-win.shtml).
Signatures, UTF-16 byte counts and ownership follow Microsoft's documentation:

- [RegCreateKeyExW](https://learn.microsoft.com/en-us/windows/win32/api/winreg/nf-winreg-regcreatekeyexw)
- [RegOpenKeyExW](https://learn.microsoft.com/en-us/windows/win32/api/winreg/nf-winreg-regopenkeyexw)
- [RegGetValueW](https://learn.microsoft.com/en-us/windows/win32/api/winreg/nf-winreg-reggetvaluew)
- [RegSetValueExW](https://learn.microsoft.com/en-us/windows/win32/api/winreg/nf-winreg-regsetvalueexw)
- [RegDeleteValueW](https://learn.microsoft.com/en-us/windows/win32/api/winreg/nf-winreg-regdeletevaluew)
- [RegDeleteKeyExW](https://learn.microsoft.com/en-us/windows/win32/api/winreg/nf-winreg-regdeletekeyexw)
- [RegCloseKey](https://learn.microsoft.com/en-us/windows/win32/api/winreg/nf-winreg-regclosekey)
