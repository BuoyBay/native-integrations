# NativePopover

A native arbitrary-content popover/flyout. It owns a
`View` that can contain ordinary native labels, fields, checkboxes, buttons,
and other supported child controls. No Canvas rendering, embedded HTML,
polling timer, or external compiled shim is used.

- **Linux:** `GtkPopover`, with native autohide, arrow, placement, keyboard
  navigation, and outside-click dismissal.
- **macOS:** transient `NSPopover` with an `NSViewController` hosting the Buoy
  content view. Native placement and dismissal are delegated to AppKit.
- **Windows:** an owned `WS_POPUP` window hosting the Buoy content HWND. The
  flyout uses a native border and native child controls, without an AppKit-style
  arrow. A thread-local message hook supplies Escape and dialog Tab/Enter
  routing; deactivation dismisses the flyout. It is not a WinUI dependency.

Copy [popover.bui](popover.bui) into your project and `Import popover`.
[example.bui](example.bui) is a runnable native text-field/checkbox popover.

## API and ownership

Construct `NativePopover(width, height)` (defaults: 280 × 160 points), then
populate its read-only `Content As View` before the first `Show`. The popover
owns that content tree. Do not add `Content` to another window/container, and
do not anchor a popover to itself or one of its content descendants. Populate
ordinary controls using `Content.AddSubview` and their normal `Move` methods.

`Show(owner As UIControl, anchor As Rect)` opens beside a rectangle in the
owner's **local graphics points**. The anchor must be finite and nonempty,
and the owner must be attached to a visible window. A hidden or disabled
owner does not open the popover. Keep an application/window property holding
the popover for as long as it is needed, just as with other reusable Buoy
integration objects. Call all methods on the GUI thread.

`Dismiss()` hides the popup and restores focus to the anchor where supported.
`Dismissed()` fires once per open session, including native dismissal; a second
`Dismiss()` is a no-op. Outside-click focus follows native platform behavior.
In the verified GTK4 adaptation, autohide consumes the dismissing click and
focus remains on the anchor; a second click activates the destination control.
Do not assume outside-click activation is identical across platforms. Native
platform behavior handles Escape when it reaches the popup. A focused GTK
Canvas can consume Escape first; its key handler must call `Dismiss()` when
that is the intended application behavior. Native callback exceptions are
contained in `LastNativeError`; exceptions from a directly called `Dismiss()`
are allowed to propagate to its caller.

`Resize(width, height)` changes the content size. `IsOpen`, `IsClosed`, and
`NativeHandle` expose current lifecycle state and the native popup handle.
Dimensions must be 1…10000 points. The first `Show` realizes the native popup;
`Dismiss` permits repeated reuse with the same content and another anchor.

`Close()` performs **terminal, idempotent cleanup** without raising
`Dismissed`. It releases the owned content (`Content` becomes `Nil`) and a
closed popover cannot be shown again. Call it in the owner's `Closed` handler,
before detaching/destroying an anchor, and before the event loop ends. The
destructor also performs it. Windows realizes the content in a hidden staging
Buoy window before transferring its HWND to the popup; cleanup restores that
native parent before releasing the staging window. Caller-owned views are
never reparented.

## Limits

This first version prefers the bottom edge and lets GTK/AppKit choose native
placement. Windows clamps a bottom placement to its monitor work area and
moves it above the anchor if needed. There is no configurable arrow edge or
animation contract. A visible popup is not automatically repositioned when an
anchor is moved; call `Show` again after such a layout change. GTK theme and
AppKit intrinsic sizes may exceed a frame too small for its child controls.

Windows geometry scales graphics points using `GetDpiForWindow`; mixed-DPI and
multi-monitor behavior still need interactive validation. The
Windows console gallery
passed visible Show, native text input after Tab, Enter handling, Escape,
outside-click dismissal and reuse. Its SSH-session contracts separately verify
hidden-owner rejection, native allocation, native callbacks and terminal cleanup.
The visibility guard remains in place. Intel macOS currently has compiler/IR
coverage only.

## Native macOS validation

ARM64 macOS **27.0.1** on `m4-vi`, using Buoy **0.72.0**, passed the native
contract executable with exit 0 and empty stderr. The test asserts actual
`NSPopover.isShown` visibility after Show and closure after Dismiss, retained
native content, resize/reuse, self-content anchor rejection, native close
callbacks, callback exception containment and terminal cleanup. The demo
also built as a native `.app`. The combined Mac gallery additionally passed real pointer opening and Escape dismissal. Physical outside-click and focus-input behavior are not covered by this programmatic run. See
macos-validation.json for source hashes and results.

Compile `smoke.bui` with `--app-type console` on macOS; the interactive demo
uses `--app-type desktop` and produces an `.app` bundle.
