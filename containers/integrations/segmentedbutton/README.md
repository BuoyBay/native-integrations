# View-based native SegmentedButton

Buoy **0.72.0** has `Toolbar.AddGroup` / `ToolbarGroup`, but no standalone
`SegmentedButton`. Its installed `documentation/xojo-shim-gaps.md` explicitly
lists `DesktopSegmentedButton` as missing. Use `ToolbarGroup` when the segments
belong in a toolbar; this integration supplies a standalone View-based control for a
window or container.

This is a native implementation, hosted in a `View`. It performs no custom
painting and installs no polling timers:

- **macOS:** AppKit `NSSegmentedControl`, with its native single, multiple and
  momentary tracking modes.
- **Linux:** GTK4 buttons in a horizontal, homogeneous `GtkBox` with the theme's
  `linked` class. Single selection uses grouped `GtkToggleButton`s, multiple
  selection uses independent toggles, and momentary mode uses `GtkButton`s.
- **Windows:** standard Win32 `BUTTON` controls. Single selection uses
  `BS_RADIOBUTTON | BS_PUSHLIKE`, multiple selection uses
  `BS_CHECKBOX | BS_PUSHLIKE`, and momentary mode uses push buttons. These are
  adjacent native buttons; they do not reproduce AppKit's continuous capsule.

The OS owns button painting, pointer tracking, focus indicators, and native
accessibility objects. Full screen-reader interaction has not been tested.
The Buoy model controls persistent selection and emits `Pressed` after updating
it. Native callbacks contain handler exceptions in `LastNativeError` rather
than allowing exceptions to unwind into the OS.

## Use

Copy [segmentedbutton.bui](segmentedbutton.bui) into your project and
`Import segmentedbutton`. There is no additional package or compiled shim.
See [example.bui](example.bui) for a complete declarative window with all three
selection modes and `With … Handle Pressed(segmentIndex As Integer)` handlers.

Add the control to its window or container, populate its segments, then call
`Open()` from the window's `Opening` handler. This ordering matters because
Buoy creates Windows container handles at attachment time. Call `Close()` from
the window's `Closed` handler; cleanup is idempotent and the destructor also
performs it. `Open()` can be called again to recreate the native controls.
On Windows, native parent destruction also invalidates the binding immediately,
so later cleanup cannot act on recycled child HWND values. A failed native
rebuild closes its partial binding before propagating the error.

After changing the host geometry through `Move` or constraints, call
`RefreshNative()`; the demo shows the window's `Resized` handler. Also call it
after changing inherited control enablement when the native child states need
refreshing. GTK respects native theme minimum sizes, so very narrow frames may
not fit their captions.

## API

- `AddSegment(caption)`, `AddSegmentAt(index, caption)`, `RemoveSegmentAt(index)`,
  `RemoveAllSegments()`, `SegmentCount`, `LastSegmentIndex`.
- `CaptionAt(index)` / `SetCaptionAt(index, caption)`.
- `SelectionStyle`: `SegmentSelectionStyle.Single` (default), `Multiple`, `None`.
- `SelectedSegmentIndex`: first selected segment, or `-1`. Setting it replaces
  the entire selection, including in Multiple mode. An empty control starts
  with no selection. Single selection allows programmatically clearing it.
- `IsSelected(index)` / `SetSelected(index, selected)`: independent selection
  in Multiple mode, exclusive selection in Single mode, no persistent state
  in None mode.
- `SegmentEnabled(index)` / `SetSegmentEnabled(index, enabled)`. Disabling a
  segment preserves its selection. Native disabled segments cannot activate.
- `Press(index)`: programmatic activation, respecting the control's `Enabled`
  and `Visible` and the segment's enablement. Raises `Pressed(index)` even when
  a Single segment was already selected. State setters do not raise events.
- `LastNativeError`: last exception caught in a native activation callback.

Indices are zero-based and invalid indices throw `OutOfBoundsException`.
Insertion/removal preserves the selected items as their indices shift;
removing the selected item clears its selection. Switching to Single retains
only the first selected item; switching to None clears all selection.
Structural edits and selection-style changes recreate native children and may
reset keyboard focus. This first version supports text and equal-width
segments. Icons, per-segment widths/tooltips, Xojo's `Segment` object API, and
macOS-specific style selection are not implemented. It is inspired by Xojo,
not a drop-in API replacement.
