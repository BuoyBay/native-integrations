# Windows desktop events

Copy `WinDesktop.bui` beside a Buoy 0.72.0 application and import it, as
`desktop-smoke.bui` demonstrates. This module receives native WinEvents through
`SetWinEventHook(WINEVENT_OUTOFCONTEXT)`; events come from the Windows desktop
event stream, rather than comparing periodic foreground-window snapshots.

`IsSupported()` is safe on every target. Construct `DesktopMonitor` on the
thread that will process its events. The default event range is
`EVENT_SYSTEM_FOREGROUND` (3). Constructor arguments are `firstEvent`,
`lastEvent`, optional process ID filter (0 means all processes), and queue
capacity (default 256, maximum 65536). Event IDs must be within
1..2147483647. A process filter is a numeric PID, not an owned process handle.

Only one monitor may be open per process. Create, use, drain and close it on
the same thread; concurrent construction is unsupported. `Close()` is
idempotent. Use `Try`/`Finally` to close explicitly. The destructor makes a
best-effort close, but Windows cannot unhook from a different thread.
The callback is a static function and never references a monitor instance;
a misplaced destructor cannot cause a callback into freed instance memory.
An unclosed hook on the wrong thread remains installed until that thread exits.

| API | Behavior |
| --- | --- |
| `Pump(maxMessages = 64)` | Bounded, nonblocking console message pump; translates and dispatches messages on the owning thread. Reposts `WM_QUIT` instead of swallowing it. |
| `DrainEvents()` | Returns queued owned `DesktopEvent` records and starts an empty queue. Does not itself pump messages. |
| `DroppedEventCount()` | Cumulative number of events dropped when the bounded queue is full or the callback encounters a Buoy exception. |
| `Close()` | Unhooks on the creating thread and clears queued events. |

GUI applications can use their existing Windows message loop and call
`DrainEvents()` from that same thread. Calling `Pump()` also dispatches other
messages owned by its thread and can reenter application window procedures;
do not call it while holding locks or while an operation cannot tolerate
reentrancy. `Pump()` dispatches at most the requested number of queued
messages per call. Native nonqueued event delivery can happen during those
message API calls as well. There is no timer, background thread, or user
callback invocation from this module.

Each `DesktopEvent` exposes `EventId`, `WindowHandle`, signed `ObjectId` and
`ChildId`, `SourceThreadId`, and `EventTimeMilliseconds`. The timestamp is a
32-bit system tick count and wraps; it is not a wall-clock timestamp.
`WindowHandle` is an unowned numeric native handle and can become invalid
before an event is drained. It must not be closed or assumed to identify the
same window indefinitely. No accessibility object or title is fetched.
When capacity is reached, newer events are dropped and existing queue order
is preserved. Exceptions are caught inside the callback so none unwind across
the C ABI boundary.

The scope is the current interactive desktop, subject to Windows session,
integrity and accessibility restrictions. It does not monitor another user's
desktop, the secure desktop, or a noninteractive service session. Native
failures throw `RuntimeException`; wrong-thread/closed-monitor usage or invalid
configuration throws `InvalidArgumentException`. Non-Windows construction
throws `UnsupportedOperationException`.

## References

Original Buoy bindings follow Microsoft's contracts for
[SetWinEventHook](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwineventhook),
[WINEVENTPROC](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nc-winuser-wineventproc),
[UnhookWinEvent](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-unhookwinevent),
[MSG](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-msg),
[PeekMessageW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-peekmessagew),
and [NotifyWinEvent](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-notifywinevent).
