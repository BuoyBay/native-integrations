# Native FontPicker

A wrapper over platform font selection. No Canvas drawing,
HTML, external shim, or new runtime dependency is involved.

- **macOS:** `NSFontManager` and the shared `NSFontPanel`. This is a modeless
  panel with live changes. `SelectionChanged(font)` fires while the user edits;
  closing the panel does not invent an OK or Cancel outcome.
- **Linux:** `GtkFontDialog`, requiring **GTK 4.10+**. `Show()` returns immediately;
  the native dialog is modal relative to its parent. `Selected(font)` fires on
  acceptance and `Cancelled()` on user cancellation.
- **Windows:** `ChooseFontW`, using the native font chooser and `LOGFONTW`.
  `Show()` runs its native modal loop and returns after acceptance/cancellation.
  `Selected(font)` or `Cancelled()` fires before it returns.

All calls must run on the GUI thread. Keep the wrapper alive while a chooser is
open, and call `Close()` when the parent window closes.

Copy [fontpicker.bui](fontpicker.bui) into your project and `Import fontpicker`.
[example.bui](example.bui) is a runnable native-button launch demo. It updates a
native Label with the chosen font.

## API

- `FontSelection(family = "Sans", size = 12, bold = False, italic = False)`:
  the shared font value, exposing `Family`, `Size` in points, `Bold`, `Italic`.
  `Copy()` returns a separate value.
- `FontPicker.Value`: initial/current selection. Both getter and setter copy
  the value, so callers cannot mutate the stored state through an alias.
  Assign before `Show()`; assigning while open throws.
- `Show(parent As Window)`: requires a native parent window. Rejects opening the
  same picker twice. Native font matching may substitute a missing font family.
- `Close()`: silent programmatic dismissal, idempotent. It does not raise
  `Cancelled`, which is reserved for a user's dialog cancellation. GTK completes
  cancellation asynchronously; pending callbacks cannot affect a reopened picker.
- `IsOpen`, `IsModeless`, `FontPicker.IsSupported()`: lifecycle/platform queries.
  Linux checks the GTK version before invoking any API added in 4.10.
- `Title`: native chooser/panel title, applied at opening.
- `LastNativeError`: errors caught at native callback boundaries, including event
  handler exceptions. GTK reports native chooser failures here. Ordinary invalid
  arguments and synchronous Win32 chooser failures throw exceptions.
- `Selected(font)`: committed GTK/Windows result.
- `SelectionChanged(font)`: live macOS result.
- `Cancelled()`: user cancelled the GTK/Windows chooser.

Sizes must be finite and greater than zero, with a maximum of 1000 points.
Family names must be nonempty. Windows family names must fit the native
31-UTF-16-unit field; long names are rejected instead of truncated. The shared
value intentionally covers family, point size, bold and italic. Underline,
strikeout, text color, OpenType features and variable-font axes are not part of
this version's API. The AppKit target requests only face, size and collection
controls through `validModesForFontPanel:`; typographic-effect actions are ignored.

The AppKit font panel is an application singleton. This wrapper permits one
active FontPicker and temporarily installs its target/action. On close it
restores the previous target, action and panel title if its target still owns
that native state. It does not hide or overwrite a panel another native
consumer has taken over. Avoid interleaving other direct font-panel APIs while
this wrapper owns it.
