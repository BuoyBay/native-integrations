# Linux content types and icon metadata

`linuxcontent.bui` is an original Buoy integration with GLib/GIO. Copy the
module beside your source and import `linuxcontent`, optionally with an
alias as demonstrated by `content-smoke.bui`.

The feature idea came from the MIME/icon helpers in
[Monkeybread's Linux plugin catalog](https://www.monkeybreadsoftware.net/pluginpart-linux.shtml).
No Monkeybread implementation or plugin is used.

| API | Result |
| --- | --- |
| `IsSupported()` | True for a Linux target. |
| `IsAvailable()` | Whether the three required shared libraries can be loaded on Linux. |
| `GuessFilename(filename)` | `ContentGuess`, containing `ContentType` and `IsUncertain`. Uses the filename only; never opens or reads the file. |
| `MimeType(contentType)` | `Optional Of String` containing the corresponding MIME type. |
| `FromMimeType(mimeType)` | `Optional Of String` containing a content type. |
| `Description(contentType)` | Human-readable, potentially localized description. |
| `GenericIconName(contentType)` | Optional freedesktop generic icon name. |
| `IconString(contentType)` | Optional serialized `GIcon`, potentially including theme fallback names. |

An icon name or serialized `GIcon` is metadata. It is not a bitmap or a
guaranteed path to an icon file. Rendering requires an icon theme and UI
integration. `IconString` uses GIO's serialization format; treat it as
opaque rather than splitting or assuming it is a file path.

The functions run headlessly without GTK, a display, D-Bus, desktop
handlers, or applications registered for a MIME type. They query the
installed shared MIME database, so classifications, descriptions and
icon metadata can vary between systems. A filename guess is advisory,
not proof of file contents or a security check. On Linux with a non-UTF-8
filename encoding, this module's UTF-8 strings cannot represent every
native filename.

## Dependencies and behavior

Install GLib/GIO >= 2.34 and `shared-mime-info`. Debian/Ubuntu runtime
packages are `libglib2.0-0t64` on current releases (or `libglib2.0-0` on
older releases) and `shared-mime-info`. The module loads versioned
`libgio-2.0.so.0`, `libglib-2.0.so.0`, and `libgobject-2.0.so.0` using
`Optional Declare`; development packages and linker symlinks are not
required. Deploy the compiler's complete output directory as usual.

`IsAvailable()` tests library loading, not every symbol or database
entry. A missing library or export throws `LibraryUnavailableException`.
All metadata operations throw `UnsupportedOperationException` on
non-Linux targets. `IsSupported()` and `IsAvailable()` remain safe there.
Empty inputs are rejected with `InvalidArgumentException`; UTF-8 bytes
are checked for embedded NUL before calling native functions.

Buoy 0.72.0 currently converts `String.Chr(0)` to an empty string and
truncates decoded strings at embedded NUL. The module cannot detect data
already removed by the language runtime. The smoke therefore tests empty
input rejection without claiming an embedded-NUL round trip.

Returned text is copied using `CString` to `String` conversion before
the native allocation is freed with `g_free()` in `Finally`. The native
`GIcon` is released with `g_object_unref()` in `Finally`, including when
serialization or text conversion fails. No native handle escapes the
module. Optional values preserve native NULL results. Required text
unexpectedly returned as NULL raises `RuntimeException`.
