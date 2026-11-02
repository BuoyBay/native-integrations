# Native tooltips

`NativeTooltip` adds operating-system hover help to any Buoy `UIControl` with a
native widget. Tested with Buoy **0.72.0**. It uses GTK4 widget tooltips,
AppKit `NSView.toolTip`, and the Win32 tooltip common control. There is no
custom drawing, web view, polling timer, extra package, or compiled shim.

Copy [tooltip.bui](tooltip.bui) into your project and `Import tooltip`. The
[runnable demo](example.bui) attaches independent tooltips to a native Button
and TextField and updates one while the application is running.

## API and lifecycle

- `Attach(owner As UIControl, text As String)`: attach after the control is
  added to a window. Windows creates some native control handles lazily, so
  the window's `Opening` handler is a good place to do this. The owner is weak;
  retain the `NativeTooltip` in a window/application property.
- `Text As String`: update help immediately. An empty string suppresses the
  tooltip while keeping the attachment. Assigning text before attachment is
  allowed; `Attach` supplies the initial attached text explicitly.
- `Refresh()`: reapply text or reattach if the owner rebuilt its native widget.
  Call this after changes such as TextField multiline mode that replace the
  native handle. Ordinary resizing does not require refreshing.
- `Owner As UIControl`, `IsAttached As Boolean`: read-only attachment state.
  Attachment does not imply the control is currently visible or hovered.
- `Close()`: detach and release native resources; safe to call repeatedly.
  Call it from the window's `Closed` handler. The destructor also cleans up.
  `Text` is retained for reuse after detachment.
- `LastNativeError`: last native attachment/update/cleanup callback exception.
  Direct native operation failures also throw to the calling Buoy code.

Only one `NativeTooltip` from this integration may attach to a native widget
at a time. A conflicting attachment is rejected before the previous attachment
is changed. Multiple different controls can have independent tooltips.
All calls must run on the GUI thread.

Tooltips never set `AccessibleHint`, `AccessibleLabel`, role, or focus state.
Applications retain control of their screen-reader descriptions. Disabled,
hidden, and keyboard-triggered tooltip behavior follows the platform.

On GTK/AppKit, the helper remembers the previous native tooltip and restores it
on `Close`, provided other code has not replaced its current text. It retains
the native widget while attached so cleanup is safe even if the parent window
has already closed. On Windows, the helper keeps a Unicode text buffer alive for the standard
native tooltip HWND; an owner-window destruction observer destroys that popup and
clears stale handles. No Buoy object is strongly retained by a native callback.
Attaching to the same owner from a different tooltip system at the same time
is outside the helper's ownership contract.
