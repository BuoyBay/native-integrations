# View-based native separators and activity indicators

Two small View-based controls (`NativeSeparator` and `ActivityIndicator` inherit `NativeIndicatorControl Inherits View`), with no custom drawing,
HTML, polling timers, WinUI, or Libadwaita dependency.

- `NativeSeparator`: `GtkSeparator` on Linux, `NSBox` with separator style on
  macOS, and a Win32 `STATIC` with `SS_ETCHEDHORZ` / `SS_ETCHEDVERT` on Windows.
- `ActivityIndicator`: `GtkSpinner` on Linux, spinning `NSProgressIndicator` on
  macOS, and a standard Win32 marquee progress control on Windows. The Windows
  presentation is a native **bar**, because classic Win32 has no stock spinner.

Copy [nativeindicators.bui](nativeindicators.bui) into your project and
`Import nativeindicators`. [example.bui](example.bui) is a complete declarative
window with horizontal/vertical separators and Start/Stop buttons.

## API and lifecycle

Add the controls to their Window/View before calling `Open()`, normally from
`Opening`. Windows creates the container HWND lazily. Call `RefreshNative()`
after geometry or inherited `Enabled` changes, as shown in the demo's `Resized`
handler. Call `Close()` from the window's `Closed` handler. Cleanup is
idempotent and is also performed by the destructor. The controls may be reopened while their native parent still exists.
All operations belong on the GUI thread.

`NativeSeparator.Orientation` is `SeparatorOrientation.Horizontal` (default)
or `Vertical`. Invalid enum values throw `InvalidArgumentException`. A separator
is centered on its host's cross-axis with a two-point native control thickness;
set the frame's long axis to the length you want. Changing orientation after
opening recreates the native child. The host is `AccessibleHidden = True` by
default because the separator is decorative.

`ActivityIndicator.Start()` requests animation; `Stop()` stops it. `IsRunning`
reports the requested state, including when `Start()` precedes `Open()`. Calling
`Open()` again preserves the requested animation state. `Close()` stops animation
and clears the running state, so reopening a closed indicator starts stopped.
Animation timing, rendering, stopped appearance, and reduced-motion behavior are
owned by the native toolkit. Windows stops its marquee.
This control does not represent a percentage or determinate progress.

Both controls inherit `IsOpen`, `NativeControlHandle` (read-only native escape
hatch), and `LastNativeError` (native creation errors, also thrown to the caller).
Windows activity indicators create and remove a unique temporary activation
manifest to opt into the OS's Common-Controls v6. This is necessary because the
Buoy 0.72 executable manifest does not declare that dependency. The activation
context is scoped to native progress-control creation; it does not change the
whole application's styling. No manifest file needs deployment. Applications
can optionally set `WindowsManifestPath` to use their own activation manifest.
Windows observes `WM_NCDESTROY` so parent destruction invalidates the stored
child handle before later cleanup or refresh can touch a recycled HWND. A control
whose native parent was destroyed must be replaced with a new instance; `Open()`
rejects reusing the stale host object.

Do not retain or reparent `NativeControlHandle`, destroy it yourself, or use it
after `Close()`. The inherited `NativeWidget` is the **Buoy host** rather than
the indicator itself. `NativeIndicatorControl` is the common lifecycle base;
construct one of the two concrete controls.
