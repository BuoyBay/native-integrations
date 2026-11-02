# Native ColorPicker

Native system color selection without custom drawing,
HTML, extra packages, or compiled shims. Copy `colorpicker.bui` into the project
and `Import colorpicker`. [example.bui](example.bui) is a complete native-button
launch demo.

The API preserves the native interaction model:

- **Linux:** `GtkColorDialog` (GTK **4.10+**), a modal chooser that completes
  asynchronously. `Show(parent)` returns immediately. Select raises `Accepted`;
  Cancel, Escape, or window close raises `Cancelled`. GTK versions below 4.10
  are rejected before the newer entry points are called. No deprecated chooser
  or custom fallback is silently substituted.
- **Windows:** Win32 `ChooseColorW`, a modal chooser. `Show(parent)` blocks while
  the native dialog runs its message loop and returns after `Accepted`,
  `Cancelled`, or `Failed`. The dialog is RGB-only; alpha requests are explicitly
  rejected. The native custom-color palette is retained for the picker's life.
- **macOS:** the shared AppKit `NSColorPanel`, a modeless **live panel**.
  `Changed` delivers live color changes; `PanelClosed` means the panel closed.
  There is no invented Accept/Cancel step. The integration observes native color
  notifications and does not replace the panel's target, action, or delegate.
  Its previous title and alpha-control visibility are restored at cleanup.
  One instance from this module may own the shared panel at a time; applications
  using their own NSColorWell/panel routing must coordinate this shared UI.

## API

- `SelectedColor As Color`: initial/current color, copied on get and set so
  mutating a returned `Color` does not modify the picker. Channels must be finite
  and within `[0,1]`; Nil is rejected. Assignment is silent. While a chooser is
  open, assignment is rejected; a live macOS panel can be updated silently.
- `WithAlpha As Boolean`: default False; set before Show. Windows rejects True.
- `SupportsAlpha As Boolean`: False on Windows, True on GTK/macOS.
- `Title As String`: applied when Show opens the native UI.
- `Interaction As ColorPickerInteraction`: `AsyncChooser`, `ModalChooser`, or
  `LivePanel`. This makes the platform difference available without target tests.
- `IsOpen As Boolean`, `LastNativeError As String`.
- `Show(parent As Window)`: requires a native parent window. Keep the picker in
  a window property while it is active. GTK/Win32 associate the chooser with this
  parent; AppKit uses its application-wide shared panel rather than a sheet.
- `Close()`: silent, idempotent dismissal and cleanup. Call from the owner's
  `Closed` handler. The destructor also calls it. Closing a GTK chooser cancels
  the pending operation; its completion callback still drains and frees native
  resources, without delivering an event to the closed or destroyed picker.

Events:

- `Accepted(value As Color)` and `Cancelled()` — GTK/Windows chooser outcome.
  Cancellation preserves the last selected color.
- `Changed(value As Color)` and `PanelClosed()` — macOS live-panel behavior.
- `Failed(message As String)` — native chooser errors. `LastNativeError` also
  records exceptions caught in native callbacks, including application handlers.

No poll timer or global keyboard/mouse hook is installed. Native dialogs own
input, focus, color UI, accessibility, and dismissal. Screen-reader interaction
has not been independently validated.
