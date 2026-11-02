# View-based native SearchField

A View-based native search entry, using native text editing and
native controls throughout. No Canvas painting, WebView, polling timer, WinUI
host, or additional compiled shim is involved.

- **macOS:** `NSSearchField`, including its native search and clear button cells.
  A delegate receives live edits; its action commits a search.
- **Linux:** GTK4 `GtkSearchEntry`, with its native search and clear icons.
  `GtkEditable::changed` provides immediate changes rather than GTK's delayed
  `search-changed` signal. `activate` commits and `stop-search` cancels.
- **Windows:** standard Win32 `EDIT` plus a native **Clear** button. Windows'
  classic controls do not provide an equivalent standalone search widget, so
  these controls are composed inside the Buoy View. `EN_CHANGE` receives edits;
  an edit subclass handles Return/Escape while leaving native text editing and
  IME processing in place. There is no painted search icon.

Copy [searchfield.bui](searchfield.bui) to a project and `Import searchfield`.
[example.bui](example.bui) is a complete runnable demo using a declarative window
and `With … Handle` event handlers.

## Lifecycle and layout

`SearchField Inherits View`, so it can be attached wherever a Buoy View is
accepted. Add it to its parent before calling `Open()` (normally from the
window's `Opening` handler). Windows creates its native container lazily at
attachment time. Set `Text` and `Placeholder` before or after opening.

Call `RefreshNative()` after a geometry or inherited `Enabled` change. The demo
shows this in its window's `Resized` event. GTK enforces its native theme's
minimum size. The Windows edit and clear button scale using their window DPI.
`FocusSearch()` focuses the actual text editor; the host View is not the editor.

Call `Close()` in the window's `Closed` handler. Cleanup is idempotent and the
destructor also performs it. Text is preserved when closing and reopening. Windows host and child destruction
notifications invalidate saved handles before Windows can recycle them; retaining
a SearchField after native parent destruction is safe for reading its last text,
refreshing, and closing. After observed host destruction, `Open()` rejects
reopening; create a new SearchField for the new window.
Native callbacks hold weak registry references and contain application handler
exceptions in `LastNativeError`, preventing exceptions from crossing the OS
callback boundary. `EntryHandle` exposes the actual native editor for advanced
interop/testing; it is invalid after closing. Do not retain or reparent it.

## API and events

- `Text As String`: reads the live editor. Assignment is silent, matching Buoy's
  standard TextField convention. Programmatic assignment does not search.
- `Placeholder As String`: native placeholder/cue text, default `"Search"`.
- `SearchChanged(query As String)`: user edits, or `Clear()` when text changes.
  Replacing text via raw native APIs can produce intermediate changes on GTK;
  use `Text` for silent programmatic replacement.
- `SearchCommitted(query As String)`: Return or native search-button activation,
  or `CommitSearch()`. An empty query is a valid commit. Applications decide
  whether to ignore it.
- `SearchCancelled()`: Escape or `CancelSearch()`. Cancellation clears first,
  emitting `SearchChanged("")` if needed, then `SearchCancelled()`.
- `Clear()`: clears and emits one change if nonempty. The native clear button
  also clears without committing or cancelling the search session.
- `CommitSearch()` / `CancelSearch()`: suppressed while this control is hidden
  or disabled. `Clear()` and `Text` remain usable programmatically.
- `Open()`, `Close()`, `IsOpen`, `RefreshNative()`, `FocusSearch()`.
- `LastNativeError`: last exception contained at a native callback boundary;
  reset when opening.

The native OS owns editing, selection, clipboard commands, focus appearance,
and IME composition. Windows Return/Escape auto-repeat is coalesced, and Return
while an IME composition is active is left to the IME. Native text controls
supply their own accessibility objects; full screen-reader behavior has not
been validated. `AccessibleLabel` on the outer Buoy View is not automatically
forwarded to the inner native editor.

This first version does not implement suggestions, query history, completion,
search scopes, custom fonts, or a debounce setting. Applications can debounce
`SearchChanged` themselves without replacing the native editor. The Windows
placeholder uses `EM_SETCUEBANNER`, which requires the normal common-controls v6
activation context.
