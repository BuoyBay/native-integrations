# View-based native ScrollView

A reusable View-based scrolling viewport, with an ordinary `View`
as its document. Native text fields, buttons, images, and other controls remain
native children inside the scrolling content. The implementation does not draw
its own controls, scrollbar tracks, or viewport.

- **macOS:** `NSScrollView`, its native clip view and native scrollers.
- **Linux:** GTK4 `GtkScrolledWindow` and its native adjustments/viewport.
- **Windows:** the Buoy host's native child HWND with standard nonclient
  horizontal/vertical scrollbars. A window subclass handles native scrollbar
  commands and wheel messages and moves the native document HWND. Wheel distance
  respects the system's configured lines/characters per notch.

Copy [scrollview.bui](scrollview.bui) into a project and `Import scrollview`.
[example.bui](example.bui) is a complete runnable demo with thirty native child
buttons, wheel scrolling, and programmatic navigation to the document's end.

## API and lifecycle

- `Content As View`: the owned document view. Add children with ordinary Buoy
  `Content.AddSubview`. Do not attach this view to another parent or move it
  yourself while the scroller is open.
- `ContentWidth`, `ContentHeight`: document extent in logical points, each from
  1 through 10,000,000. Use these properties to resize the document.
- `HorizontalScrolling`, `VerticalScrolling`: both default to True. Disabling
  an axis resets its offset to zero.
- `AutoHideScrollbars`: defaults to True. False requests visible scrollbars on
  enabled axes. System overlay-scroller behavior can still affect appearance.
- `ScrollTo(x, y)`: scroll in logical points, clamped to the scrollable range.
  Negative values clamp to zero; NaN, infinity, or huge offsets are rejected.
- `OffsetX`, `OffsetY`: current native scroll position, including user wheel and
  scrollbar movement. GTK reads the actual adjustments and macOS the clip view;
  Windows updates them through native messages. No polling timer is installed.
- `Open()`, `Close()`, `IsOpen`, `RefreshNative()`, `LastNativeError`.

Populate `Content`, attach the ScrollView to a window or container, and call
`Open()` in the window's `Opening` handler. Windows needs this order because
Buoy creates child HWNDs at attachment time. Call `RefreshNative()` after
changing the host frame or applying constraints. Content extent and scrollbar
property setters refresh automatically. Call `Close()` from `Closed`; cleanup
is idempotent and also runs in the destructor.

The Content object and its children survive Close/Open, as do the logical
scroll offsets. GTK queues a requested position until its first native
allocation if ScrollTo is called before the viewport is mapped. A scroll after
an extent change may clamp to the currently allocated native range; for initial
positioning, request the position once the window is shown.

On Windows, destroying the host or its parent invalidates its stored HWNDs on
`WM_NCDESTROY`. Refresh/Close remain safe afterwards, and Open rejects reopening
that destroyed host; create a new ScrollView for a new window.

Native APIs retain the document across reparenting. Buoy's wrapper retains its
original logical parent, which is why application code should size the document
through ContentWidth/ContentHeight rather than Content.Move. The native content
is reattached to its original host on Close when that host is still available.

## Native macOS validation

ARM64 macOS **27.0.1** on `m4-vi`, using Buoy **0.72.0**, passed native
contract execution with exit 0 and empty stderr. This exercises native
NSScrollView creation, direct NSClipView scrolling and readback, clamping,
disabled axes, retained child text, close and reopen. The demo also built as
a native `.app`. The combined Mac gallery also passed real scrolling-button and child-row activation. Physical trackpad/wheel input is not covered by these runs. macos-validation.json records source hashes,
compiler results and native execution provenance.

Build the `smoke.bui` contract on macOS with `--app-type console`; build the
demo with `--app-type desktop`. Explicit console mode prevents subclass-based
contract programs from being automatically bundled as desktop applications.
