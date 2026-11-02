# Linux Secret Service passwords

Copy `linuxsecrets.bui` into a Buoy 0.72.0 project and use `Import linuxsecrets As SecretInterop`.
It integrates with password managers exposing the freedesktop Secret Service
through libsecret, such as GNOME Keyring. It does not integrate directly with
every password-manager product or read browser password databases.

| API | Behavior |
| --- | --- |
| `IsSupported()` | Whether the build targets Linux |
| `IsAvailable()` | Whether versioned libsecret and GLib libraries load; does not connect to a service |
| `Store(application, key, label, password, sessionOnly = False)` | Store/update a scoped UTF-8 text password; optionally use the session-only collection |
| `Lookup(application, key)` | Owned `Optional Of String`; absent differs from an empty password |
| `Clear(application, key)` | Delete all unlocked matching entries; returns whether any were removed |

Every operation uses all three attributes: fixed `xdg:schema` value
`org.buoy.Integrations.Password`, `buoy-application`, and `buoy-key`.
Use a stable reverse-domain application identifier and a specific nonempty key.
Labels, attributes, and application identifiers are metadata, not encrypted
secrets. Store only the password in the password argument. No enumeration API
is provided. Clearing a key can delete multiple duplicate unlocked items with
the same exact attributes, following libsecret's native contract.

These synchronous calls may activate the user's Secret Service, prompt to
unlock a keyring, or block indefinitely. Call them from a worker appropriate
to your application. `IsAvailable()` does not establish that a Secret Service
is running or unlocked. Default storage uses the service's `default`
collection; `sessionOnly = True` uses its nonpersistent `session` collection.
The module does not request, collect, or supply a keyring master password.

## Requirements and ownership

Requires 64-bit glibc Linux, `libsecret-1.so.0`, `libglib-2.0.so.0`, a session
D-Bus and a Secret Service for live operations. Debian/Ubuntu package
`libsecret-1-0` supplies the client library; a backend such as `gnome-keyring`
is separate. `Optional Declare` uses versioned libraries and requires no
development symlinks or linker import stubs. Missing libraries/exports throw
`LibraryUnavailableException`; service errors become `RuntimeException` with
native GError code in `ErrorCode` and numeric domain/code in the message.
GError codes are domain-specific, not Linux errno. Native error text and secret
content are not included in exception messages.

The nonvariadic `*_v_sync` functions receive a GLib string-keyed hash table;
the schema argument is NULL, as permitted by libsecret, and explicit attributes
provide the module's namespace. GLib owns duplicated attribute keys/values;
the table is released in `Finally`. Returned passwords are copied through
`CString` validation and freed with `secret_password_free` in `Finally`.
Native GErrors are freed. Ordinary Buoy strings hold plaintext copies and do
not provide guaranteed zeroization or protection from process memory readers.

Application/key/label must be nonempty. Passwords may be empty. Inputs are
checked for zero UTF-8 bytes; Buoy 0.72.0 already truncates decoded strings at
NUL and makes `String.Chr(0)` empty, so data removed before the call cannot be
detected. This API is for UTF-8 text passwords, not arbitrary binary secrets.
On other targets only availability/platform queries are usable; operations
throw `UnsupportedOperationException`.

## Native contracts

Signatures and ownership follow official libsecret documentation:

- [Store attribute vector](https://gnome.pages.gitlab.gnome.org/libsecret/func.password_storev_sync.html)
- [Lookup attribute vector](https://gnome.pages.gitlab.gnome.org/libsecret/func.password_lookupv_sync.html)
- [Clear attribute vector](https://gnome.pages.gitlab.gnome.org/libsecret/func.password_clearv_sync.html)
- [Free returned passwords](https://gnome.pages.gitlab.gnome.org/libsecret/func.password_free.html)
