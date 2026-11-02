# Linux desktop property events

`linuxdesktop.bui` provides a dedicated X11 event connection. Copy it beside
your entry file and import `linuxdesktop`; `desktop-smoke.bui` demonstrates
construction, bounded event draining, and `Close()` in `Finally`.

| API | Behavior |
| --- | --- |
| `IsSupported()` | Whether the compiler target is Linux. |
| `IsAvailable()` | Whether `libX11.so.6` loads and the default X display can be opened. |
| `New DesktopMonitor` | Open a private connection and subscribe to root-window property changes on the default screen. |
| `monitor.Drain(limit = 256)` | Return owned `DesktopEvent` records from queued notifications; process at most 1–4096 events per call. |
| `monitor.Close()` | Release the connection. Idempotent; later `Drain` calls fail. Destructor also closes it. |

Each event contains `PropertyName`, `WindowId`, `TimestampMilliseconds`,
`IsDeleted`, and `IsSynthetic`. Boolean helpers classify the EWMH properties
`_NET_ACTIVE_WINDOW`, `_NET_CURRENT_DESKTOP`, `_NET_CLIENT_LIST`, and
`_NET_CLIENT_LIST_STACKING` as active-window, workspace, or window-list
changes. All other root property changes are returned too.

These are real `PropertyNotify` events delivered by the X server, not periodic
comparisons of desktop state. The record reports which property changed; it
does not include the property's value or guarantee a later read observes the
same value. A property may change repeatedly between drains. The X timestamp
is a server-relative millisecond counter with 32-bit wrap semantics, not a
wall-clock timestamp. Atom names follow X11's Latin-1 STRING convention;
the standard EWMH names are ASCII.

`Drain` checks `XPending` before `XNextEvent`, so it does not wait for a new
event. Xlib calls can still perform socket IO and server round trips (for
example, atom-name lookup); this API is not a nonblocking socket abstraction.
Use one thread and consumer per monitor. It owns its connection and does not
change another client's event selection, intercept keyboard/mouse input, or
install a global Xlib error handler.

## Requirements and limitations

Supports 64-bit x86-64 and ARM64 Linux with `libX11.so.6` and an accessible
default `DISPLAY`/Xauthority session. Development symlinks are unnecessary.
X11's native event union is 192 bytes on these LP64 ABIs; the property-event
prefix is 64 bytes. Native handles never escape the module. Atom-name memory
is copied and freed with `XFree` in `Finally`.

This is an X11 integration. A Wayland session may expose Xwayland, but that
only exposes the Xwayland root and clients; it does not provide complete
Wayland desktop events. EWMH classifications require a cooperating window
manager, and only the display's default screen is monitored. There are no
clipboard, hotkey, notification-action, or session-lock callbacks here.

Unavailable libraries throw `LibraryUnavailableException`; failure to open
the display or use a closed monitor throws `RuntimeException`. An invalid
drain limit throws `InvalidArgumentException`. Operations on other platforms
throw `UnsupportedOperationException`, while capability functions return
false. Xlib's default asynchronous protocol/connection-error policy remains
in effect: losing the X server can terminate the process rather than raise
a Buoy exception. Do not treat `IsAvailable()` as a permanent connection
guarantee.
