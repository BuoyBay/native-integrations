# TextInputCanvas with IME and custom drawing

A Canvas-based custom text-input control and a small plain-text editor (`TextEditor Inherits TextInputCanvas`), inspired by [Einhugur/Xojo TextInputCanvas](https://bitbucket.org/einhugur/textinputcanvas/src/master/).
This is an independent implementation, not a source-compatible Xojo plugin.
No Xojo SDK or additional package is required.

The reference inspected was upstream commit
`f9055eda24fe12a7e858c7d272d140feb9c88105` (2.2). Its
[documented contract](https://api.bitbucket.org/2.0/repositories/einhugur/textinputcanvas/src/f9055eda24fe12a7e858c7d272d140feb9c88105/Docs/Docs.xml)
separates committed text, incomplete input, selection, document queries, commands,
and custom drawing. This component follows that separation; upstream source is
not included.

## Files

- `textmodel.bui`: `TextRange` and `TextDocument`, independent of the GUI runtime.
- `textinputcanvas.bui`: subclassable `TextInputCanvas` and GTK4 IME adapter.
- `inputbridge.bui`: native callback contract and UTF-16/codepoint conversions.
- `nativewindows.bui`: Windows IMM adapter and native character/shortcut handling.
- `nativemacos.bui`: macOS `NSTextInputClient` adapter.
- `texteditor.bui`: working multiline `TextEditor` with replaceable drawing.
- `editorwheel.bui`: native wheel adapter for browsing independently of the caret.
- `wheel-smoke.bui`: wheel delivery, fractional scrolling, caret reveal and lifecycle regression.
- `example.bui`: standalone GUI demo using `TextEditor`.
- `model-smoke.bui`: console assertions for Unicode editing, composition and history.
- `contract-smoke.bui`: GUI-runtime assertions for event dispatch and adapter lifecycle.
- `native-smoke.bui`: synthetic Windows-message and native macOS-protocol assertions.
- `gtk-callback-smoke.bui`: GTK exception containment, disconnect and registry-reuse assertions.

Copy `textmodel.bui`, `textinputcanvas.bui`, `texteditor.bui`, `inputbridge.bui`,
`nativewindows.bui`, `nativemacos.bui` and `editorwheel.bui` into your Buoy project. Use `Import texteditor` for
the ready-made editor, or `Import textinputcanvas` and `Import textmodel` to
implement your own document and renderer. The checked [demo](example.bui) shows
window setup, input-method attachment, focus, change events and cleanup.

## Run the demo

Use the project's desktop image for Linux GUI dependencies. With the desktop
running as described in the root README:

```sh
docker compose --env-file /dev/null exec desktop sh -c '
  set -eu
  project=$(mktemp -d)
  cp /workspace/integrations/textinput/*.bui "$project/"
  cd "$project"
  mkdir -p out
  buoy example.bui --check --diagnostic-format json
  buoy example.bui -o out/editor
  ./out/editor
'
```

Buoy 0.72.0 requires the output directory to exist before compilation to reliably
copy its runtime libraries. Distribute the entire `out` directory.

Click to place the caret, drag to select, or use Shift with arrow/Home/End keys.
Primary+A/C/X/V select all/copy/cut/paste; Primary+Z undoes,
Primary+Shift+Z or Primary+Y redoes. Primary is Ctrl on Linux/Windows and Command
on macOS. Return inserts a newline; Tab remains available for focus traversal.
The caret scrolls into view as you edit or navigate. Mouse wheels and trackpads browse
both axes without moving the caret; repainting preserves that viewport. `ScrollBy`
accepts logical points, while `NativeWheel` distinguishes precise point deltas from
wheel lines. Both stop at the content bounds and leave unchanged scrolling available
to an enclosing viewport. `OpenInputMethod`/`CloseInputMethod` also attach/detach the
editor wheel adapter.

On Linux, try **Ctrl+Shift+U**, release the modifiers, type `1f600`, and press
Return: the GTK input method commits an emoji. Escape cancels pending input.
Configured GTK input methods can provide other input sequences.

## Custom editor contract

Subclass `TextInputCanvas` and handle these events:

| Event | Responsibility |
| --- | --- |
| `Draw(g)` | Draw the document, selection, caret and incomplete text in canvas-local coordinates. Graphics is valid only during this event. |
| `IsEditable()` | Return whether native or keyboard input may change the document. Without a handler, editing is disabled. |
| `InsertText(text, range)` | Replace `range`, or the current selection when it is `Nil`. Clear incomplete text after committing. |
| `SetIncompleteText(text, replacementRange, relativeSelection)` | Display temporary composition without mutating committed text. The GTK backend supplies a `Nil` replacement range and the composition cursor as relative selection. |
| `DiscardIncompleteText()` | Clear temporary input, preserving the committed document and selection. |
| `SelectedRange()` | Return the normalized selection; a zero-length range is an insertion point. |
| `CaretIndex()` | Return the active end of selection, including for backwards selections. |
| `TextLength()`, `TextForRange(range)` | Expose committed document text to the input method. |
| `RectForRange(range)` | Return a `TextInputRect` in local logical pixels for the candidate-window position. The demo returns the active caret rectangle. |
| `CharacterAtPoint(x, y)` | Hit-test local coordinates to a document codepoint index. |
| `SelectionRequested(position, extendSelection)` | Apply a click or drag selection. |
| `DoCommand(command, extendSelection)` | Execute a command and return whether it was handled. |
| `GotFocus()`, `LostFocus()` | Native input-focus notifications. |

### Command vocabulary

`DoCommand(command, extendSelection)` receives these Buoy command names (not Xojo's
`Cmd…` constants). The native adapters translate each OS's own key bindings into
them, and `PerformCommand` lets application code issue them. A handler returns
`False` for commands it does not implement; the adapters then leave the key to
the platform (Tab keeps focus traversal). `extendSelection` is `True` for every
Shift / AppKit `…AndModifySelection:` variant and applies to every `move…` and
`page…` command.

| Group | Commands |
| --- | --- |
| Caret | `moveLeft`, `moveRight`, `moveUp`, `moveDown`, `moveWordLeft`, `moveWordRight` |
| Line | `moveHome` (editor's choice; Studio toggles first non-blank / column 0), `moveEnd`, `moveLineStart` (always column 0), `moveLineEnd` |
| Paragraph (logical line) | `moveParagraphBackward` / `moveParagraphForward`: to this line's start/end, or the previous start / next end when already there |
| Document | `moveDocumentStart`, `moveDocumentEnd` |
| Page (caret and view) | `pageUp`, `pageDown` |
| View only (caret stays) | `scrollPageUp`, `scrollPageDown`, `scrollLineUp`, `scrollLineDown`, `scrollDocumentStart`, `scrollDocumentEnd`, `centerSelection` |
| Selection | `selectAll`, `selectNone`, `selectLine` (with its line break), `selectWord` |
| Deletion | `deleteBackward`, `deleteForward`, `deleteWordBackward`, `deleteWordForward` |
| Kill and yank | `deleteToLineStart`, `deleteToLineEnd` (with nothing to delete before/after the caret, the line break), `yank` (inserts the kill buffer) |
| Insertion | `insertNewline` (editor newline, may auto-indent), `insertLineBreak` (bare `\n`), `openLine` (break after the caret, caret stays), `insertTab`, `insertBacktab`, `transpose` |
| Clipboard and history | `copy`, `cut`, `paste`, `undo`, `redo` |
| Multiple cursors (optional) | `addCursorAbove`, `addCursorBelow`, `addNextOccurrence`, `skipOccurrence`, `selectAllOccurrences`, `columnSelectUp`, `columnSelectDown`, `columnSelectLeft`, `columnSelectRight`, `cursorsAtLineEnds`, `collapseSelections` (returns `False` with one cursor, so Escape keeps its meaning), `undoCursor`, `chordPrefix` (Primary+K: the next command is the chord's second key) |
| Lines (optional) | `copyLinesUp`, `copyLinesDown` (`duplicateLines` is `copyLinesDown`) |

The reference `TextEditor` implements `selectAll`, `copy`, `cut`, `paste`, `undo`,
`redo`, `deleteBackward`, `deleteForward`, `moveLeft`, `moveRight`, `moveUp`,
`moveDown`, `moveHome`/`moveLineStart`, `moveEnd`/`moveLineEnd`,
`moveDocumentStart` and `moveDocumentEnd`. Buoy Studio's `StudioCodeEditor`
implements the whole vocabulary (plus its own `indent`, `toggleComment`, … commands);
the kill buffer is shared by all its editors and consecutive kills at one place
accumulate, as in `NSTextView`. Forward word motion stops at the word end on macOS
and Linux and at the next word's start on Windows.

### Multi-cursor and drag and drop (StudioCodeEditor)

`StudioCodeEditor` keeps an ordered, non-overlapping set of selections with one
primary selection. `SelectionStart`, `SelectionLength`, `CaretPosition`,
`SelectedText`, `SelectRange` and the input-method contract (`SelectedRange`,
`CaretIndex`, `RectForRange`) describe the primary selection only, so adapters are
unchanged; starting an input-method composition collapses to the primary cursor.
`SelectionCount`, `GetSelections()`, `PrimarySelectionIndex`,
`SetSelections(selections, primary)`, `AddSelection(anchor, caret)` and
`CollapseSelections()` (with `StudioEditorSelection` anchor/caret pairs) expose the
rest. Every editing and motion command in the vocabulary runs at each cursor;
overlapping results merge, and each command raises `TextChanged` once, so the host
records one undo step. Paste puts one clipboard line at each cursor when the line
count equals the cursor count (copy with several selections joins them with line
breaks), otherwise the whole text at every cursor. Line commands (toggle comment,
indent, move and copy lines) touch each covered line once.

| Action | macOS | Windows | Linux |
| --- | --- | --- | --- |
| Add / remove a cursor | ⌥-click | Alt+click | Alt+click |
| Column (box) selection | ⌥-drag or ⇧⌥-drag | Shift+Alt+drag | Shift+Alt+drag, middle-button drag |
| Column select by keyboard | ⇧⌥⌘ + arrows | Ctrl+Shift+Alt + arrows | Ctrl+Shift+Alt + ← / → (↑/↓ copy lines; use add-cursor) |
| Add cursor above / below | ⌥⌘↑ / ⌥⌘↓ | Ctrl+Alt+↑ / ↓ | Shift+Alt+↑ / ↓, Ctrl+Shift+↑ / ↓ |
| Add next occurrence (first press: the word) | ⌘D | Ctrl+D | Ctrl+D |
| Skip occurrence | ⌘K ⌘D | Ctrl+K Ctrl+D | Ctrl+K Ctrl+D |
| Select all occurrences | ⇧⌘L, ⌃⌘G | Ctrl+Shift+L | Ctrl+Shift+L |
| Cursors at line ends | ⇧⌥I | Shift+Alt+I | Shift+Alt+I |
| Back to one cursor | Esc | Esc | Esc |
| Copy line up / down | ⇧⌥↑ / ⇧⌥↓ | Shift+Alt+↑ / ↓ | Ctrl+Shift+Alt+↑ / ↓ |
| Copy a dragged selection instead of moving it | hold ⌥ | hold Ctrl | hold Ctrl |

`undoCursor` (VS Code's ⌘U / Ctrl+U) has no default key because Primary+U is
Studio's Run All Tests. Routing: on macOS Studio's local `NSEvent` monitor catches
these chords before `interpretKeyEvents:` (AppKit would otherwise send
`moveParagraph…AndModifySelection:` for ⇧⌥↑/↓ and insert `ˆ` for ⇧⌥I);
`StudioMacEditorCommand` is the table. On Windows Studio's window subclass sees
`WM_KEYDOWN` and `WM_SYSKEYDOWN` before the IMM adapter (which would turn
Ctrl+Alt/Shift+Alt arrows into plain motion); `StudioWindowsEditorCommand` is the
table, and Ctrl+Alt only binds arrows so AltGr text is unaffected. On Linux the
canvas `KeyDown` binds them. Primary+D is also Studio's menubar Duplicate; in Source
mode that item issues `addNextOccurrence`. Linux uses VS Code's Linux defaults and
leaves Ctrl+Alt+↑/↓ unbound, because GNOME and other desktops use it to switch
workspaces.

Drag and drop uses Buoy's `IDragSource`/`IDropTarget` on the canvas
(`RegisterDragSource`/`RegisterDropTarget`, attached by `Open()`): pressing on the
selection and dragging moves it (copy modifier: ⌥ on macOS, Ctrl elsewhere) with a
drop caret, dropping inside the selection cancels, and the move is one undo step.
The source offers the text only while a press on the selection is pending, so other
drags keep selecting. Text from other applications is inserted at the drop point;
dropped files raise `FilesDropped(files) As Boolean` and, when unhandled, insert
their paths one per line. Dragging the selection into another application is a
native drag (the original is removed when the target accepts a move). Below the
platform drag threshold, or without native drag and drop, the editor performs the
move itself from its mouse events.

While a selection drag, an in-editor text drag or a native drop hovers near an edge
of the text area (the top edge is below the sticky scope headers), a 40 ms timer
auto-scrolls, faster the further out the pointer is, and re-applies the drag at the
resting pointer. The drop indicator is a full-height bar with serifs, hidden where a
drop would be a no-op (inside the dragged selection). The pointer is an arrow over a
draggable selection and an arrow or copy cursor during an in-editor drag; Escape
cancels that drag (checked before host shortcuts). Text dragged from any
`StudioCodeEditor` in the process (another split pane or window) moves unless the copy
modifier is held; drags from other applications copy. A move whose source document
was replaced during the drop (split panes of one document) finds the dragged text
again by its recorded range and only removes it when exactly that text was inserted
once outside it. `ShowsDragImage` (off by default) supplies a card of the dragged
lines as the platform drag image: on Buoy 0.72 Linux any non-Nil `DragImage` stops the
GTK drag, and it is unverified on macOS and Windows.

### Key bindings per OS

**macOS** follows the user's AppKit key bindings (`StandardKeyBinding.dict`, plus any
`DefaultKeyBinding.dict`): `interpretKeyEvents:` produces action selectors and
`MacSelectorCommand` in `nativemacos.bui` maps them. Unmapped selectors (`noop:`,
marks, case changes) are ignored. With the default bindings:

| Keys | Selector | Command |
| --- | --- | --- |
| ←/→, Ctrl+B/F | `moveLeft:`/`moveBackward:`, `moveRight:`/`moveForward:` | `moveLeft`, `moveRight` |
| ↑/↓, Ctrl+P/N | `moveUp:`, `moveDown:` | `moveUp`, `moveDown` |
| ⌥←/⌥→ | `moveWordLeft:`, `moveWordRight:` | `moveWordLeft`, `moveWordRight` |
| ⌘←/⌘→, Ctrl+←/→ | `moveToLeftEndOfLine:`, `moveToRightEndOfLine:` | `moveHome`, `moveEnd` |
| Ctrl+A / Ctrl+E | `moveToBeginningOfParagraph:`, `moveToEndOfParagraph:` | `moveLineStart`, `moveLineEnd` |
| ⌥↑/⌥↓ | `moveBackward:`+`moveToBeginningOfParagraph:`, `moveForward:`+`moveToEndOfParagraph:` | paragraph motion |
| ⌥⇧↑/⌥⇧↓ | `moveParagraphBackward/ForwardAndModifySelection:` | `moveParagraphBackward/Forward` |
| ⌘↑/⌘↓ | `moveToBeginningOfDocument:`, `moveToEndOfDocument:` | `moveDocumentStart/End` |
| Home/End (fn+←/→) | `scrollToBeginningOfDocument:`, `scrollToEndOfDocument:` | `scrollDocumentStart/End` (view only) |
| ⇧Home/⇧End | `moveToBeginning/EndOfDocumentAndModifySelection:` | `moveDocumentStart/End`, extending |
| Page Up/Down (fn+↑/↓) | `scrollPageUp:`, `scrollPageDown:` | `scrollPageUp/Down` (view only) |
| ⌥Page Up/Down, Ctrl+V, ⇧Page Up/Down | `pageUp:`, `pageDown:` (`…AndModifySelection:`) | `pageUp`, `pageDown` |
| Ctrl+L | `centerSelectionInVisibleArea:` | `centerSelection` |
| ⌫, Ctrl+H, Ctrl+⌫ / ⌦, Ctrl+D | `deleteBackward:` (`…ByDecomposingPreviousCharacter:`), `deleteForward:` | `deleteBackward`, `deleteForward` |
| ⌥⌫ / ⌥⌦ | `deleteWordBackward:`, `deleteWordForward:` | `deleteWordBackward/Forward` |
| ⌘⌫ | `deleteToBeginningOfLine:` | `deleteToLineStart` |
| Ctrl+K | `deleteToEndOfParagraph:` | `deleteToLineEnd` |
| Ctrl+Y / Ctrl+T | `yank:`, `transpose:` | `yank`, `transpose` |
| Return / ⌥Return | `insertNewline:` (commits `\n`), `insertNewlineIgnoringFieldEditor:` | text, `insertLineBreak` |
| Ctrl+O | `insertNewlineIgnoringFieldEditor:`+`moveBackward:` | `openLine` behaviour |
| Tab / ⇧Tab | `insertTab:`, `insertBacktab:` | `insertTab`, `insertBacktab` (focus traversal when unhandled) |
| Esc | `cancelOperation:` / `complete:` | cancels composition |

⌘A/C/X/V/Z/⇧Z/Y keep Buoy's KeyDown dispatch (`selectAll`, clipboard, history).
Application-specific ⌘ shortcuts with no selector (Studio's ⌘/, ⌘], ⌘D, ⌘G, ⌘E,
⌘', ⌘K, ⇧⌘L and the multi-cursor chords below) are the application's job; Studio
catches them with a local `NSEvent` monitor.

**Windows** uses edit-control conventions, mapped from `WM_KEYDOWN` virtual keys by
`WindowsKeyCommand` in `nativewindows.bui`. Shift extends every motion.

| Keys | Command |
| --- | --- |
| ←/→, Ctrl+←/→ | `moveLeft/Right`, `moveWordLeft/Right` |
| ↑/↓, Ctrl+↑/↓ | `moveUp/Down`, `scrollLineUp/Down` (view only) |
| Home/End, Ctrl+Home/End | `moveHome/End`, `moveDocumentStart/End` |
| Page Up/Down | `pageUp/Down` |
| Backspace, Ctrl+Backspace | `deleteBackward`, `deleteWordBackward` |
| Delete, Ctrl+Delete, Shift+Delete | `deleteForward`, `deleteWordForward`, `cut` |
| Ctrl+Insert, Shift+Insert | `copy`, `paste` |
| Ctrl+A/C/X/V/Z/Y, Ctrl+Shift+Z | `selectAll`, `copy`, `cut`, `paste`, `undo`, `redo`, `redo` |
| Esc | cancels composition |

Printable keys stop at the adapter (text arrives as `WM_CHAR`). Unbound or unhandled
Ctrl combinations and non-character keys (Tab, F1–F24, Insert, navigation) continue
to the Canvas `KeyDown` event, so application shortcuts still work.

**Linux** has no binding table for custom GTK widgets: the GTK input method takes
text, and the canvas `KeyDown` event (or a subclass's) binds the rest.
`TextInputCanvas`'s default handler binds arrows, Home/End, Backspace/Delete and
Ctrl+A/C/X/V/Z/Shift+Z/Y. `StudioCodeEditor` follows GtkTextView:

| Keys | Command |
| --- | --- |
| ←/→, Ctrl+←/→ | `moveLeft/Right`, `moveWordLeft/Right` |
| ↑/↓, Ctrl+↑/↓ | `moveUp/Down`, `moveParagraphBackward/Forward` |
| Home/End, Ctrl+Home/End | `moveHome/End`, `moveDocumentStart/End` |
| Page Up/Down | `pageUp/Down` |
| Backspace, Ctrl+Backspace, Ctrl+Shift+Backspace | `deleteBackward`, `deleteWordBackward`, `deleteToLineStart` |
| Delete, Ctrl+Delete, Ctrl+Shift+Delete, Shift+Delete | `deleteForward`, `deleteWordForward`, `deleteToLineEnd`, `cut` |
| Ctrl+Insert, Shift+Insert | `copy`, `paste` (capture-phase key controller: Insert has no `KeyName`) |
| Ctrl+A, Ctrl+Shift+A or Ctrl+\\ | `selectAll`, `selectNone` |
| Ctrl+C/X/V, Ctrl+Z, Ctrl+Shift+Z or Ctrl+Y | clipboard, `undo`, `redo` |
| Tab / Shift+Tab | `insertTab` / `insertBacktab` |

`CommitText(text, range)`, `UpdateComposition(text, cursor)`,
`CancelComposition()`, `DeleteSurrounding(offset, count)` and
`PerformCommand(command, extendSelection)` are public dispatch methods useful
for adapters and application commands. Mutating input dispatch honors
`IsEditable`; application code controls any direct changes to its own model.
Call `Invalidate()` after changing the document from application code.

All document ranges and composition cursors count **zero-based Unicode
codepoints**, consistent with Buoy strings, not UTF-8 bytes or UTF-16 code units.
`TextDocument` normalizes CRLF/CR to LF, clamps ranges, keeps selection direction,
and maintains up to 100 undo snapshots. A composition commit is one history
operation. Set `Document.IsReadOnly` to disable user edits while retaining
selection and copy. A native composition may supply a replacement range independent of the current
selection; `TextDocument.SetComposition` accepts that range as optional integer
location/length arguments. The document stays unchanged until commit or cancel.
Setting `Document.Text` replaces the document and clears
history, selection and composition.

## Native input and lifecycle

**Linux:** `OpenInputMethod()` attaches a `GtkIMMulticontext` to the real
`NativeWidget`, with a capture-phase key controller. GTK filters and consumes
IME input before ordinary Canvas key handling, preventing duplicate insertion.
The adapter handles commit, preedit, focus, surrounding-text queries and
surrounding-text deletion. UTF-8 byte offsets are converted at the GTK boundary;
application-facing indices remain codepoints. GTK preedit attributes are released;
the demo draws a uniform underline rather than exposing their individual styles.
GTK 4.2 or later and Pango/GLib/GObject are required; the desktop image supplies them.
See GTK's [key-controller IM context](https://docs.gtk.org/gtk4/method.EventControllerKey.set_im_context.html)
and [surrounding text API](https://docs.gtk.org/gtk4/method.IMContext.set_surrounding_with_selection.html).

Call `OpenInputMethod()` **after `AddSubview` and before focusing** the canvas.
Call `CloseInputMethod()` from the window's `Closing` handler, before its native
widgets are destroyed. Both methods tolerate repeated calls. Active GTK callbacks
retain the canvas through a registry until closed, so explicit cleanup matters
in applications that open and close multiple editor windows. Do not pass
`NativeHandle` to GTK; it identifies Buoy's internal bridge, not the widget.

**Windows:** the adapter attaches a `SetWindowSubclass` callback to the canvas
HWND, creates and associates an owned IMM input context, and restores the previous
context on close. `WM_IME_COMPOSITION` supplies preedit and committed text;
`WM_IME_CHAR` is consumed to avoid duplicate insertion. Candidate and composition
positions follow the drawn caret, converted from logical units to physical client
pixels using `GetDpiForWindow` for per-monitor DPI awareness. `WM_CHAR` accepts UTF-16 surrogate pairs; `WM_UNICHAR` accepts scalar input.
Physical US-International dead-key composition (`é` and apostrophe+Space) and
German AltGr (`@`) pass on the Windows lab. Key-down messages are consumed before
Buoy's own `ToUnicode` dispatch can consume pending dead-key state; Ctrl
shortcuts and non-character keys (Tab focus traversal, F-keys, unhandled
navigation) still reach the Canvas `KeyDown` event. Commands use virtual
keys because Ctrl+A and similar shortcuts can produce control characters rather
than letters (see the Windows binding table above). The underlying Canvas
printable-key handler is bypassed while the adapter is attached. Native focus loss cancels pending composition.

This is an **IMM compatibility adapter**, not a TSF text-store implementation.
It requires Windows 10 version 1607 or later and an interactive GUI thread
with IMM available. In this lab,
`ImmCreateContext` works in the guest console but fails in OpenSSH's separate
session. Run interactive tests through the VM console as described below.
The US-layout tests cover native characters, composition lifecycle and preedit
retrieval populated through `ImmSetCompositionStringW`. The native smoke test
reports when that preedit API is unavailable. Actual East Asian input-method
result notifications and language-specific candidate UI have not been exercised.
See Microsoft's [composition message](https://learn.microsoft.com/en-us/windows/win32/intl/wm-ime-composition)
and [window subclassing API](https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nf-commctrl-setwindowsubclass).

**macOS:** the adapter creates a process-cached Objective-C subclass of the
canvas's native view class, preserving its ivar layout and drawing implementation.
It adopts `NSTextInputClient` and provides marked text, insertion, UTF-16 selection
and marked ranges, attributed surrounding-text queries, screen-coordinate candidate
rectangles, hit testing, text commands and responder focus notifications.
`interpretKeyEvents:` routes ordinary text, input-method events and every
AppKit key-binding selector (see the macOS binding table above); Command+A/C/X/V/Z/Y
retain Buoy's key dispatch. Detaching restores the view's original class.
The protocol exposes a virtual document containing the current marked text while
the application's committed document remains unchanged. Empty marked text clears
the native and model replacement state without deleting the original selection.
Movement commands cancel the mark before updating the selection.

The macOS implementation has passed native ARM64 builds and execution on `m4-vi`
(Apple M4 Pro, macOS 27.0.1), including model/contract tests, actual
`NSTextInputClient` protocol calls, in-process AppKit keyboard events and Quartz
canvas rendering. Command+A, Command+Z/Shift+Z, navigation/backspace, Return,
Unicode/emoji, F1 and Control+A are covered. The empty-marked-text and stale-range
regressions run natively. Intel macOS still has compiler/IR validation only.

Live tests also post global CGEvents through the explicitly approved Buoy Test
Controls app. They cover clipboard copy/cut/paste, Command+Arrow line selection,
Unicode/emoji deletion and undo, a US-layout Option+E dead key, mouse drag
selection, own-window ScreenCaptureKit capture and clean shutdown. The helper
shows live permission icons, Settings buttons and a first-click draggable app
icon. Its extensible local command client lets later tests use the same approved
app without rebuilding it. See the helper guide.
Real Japanese Romaji IME preedit, candidate-panel navigation/commit, selected
emoji replacement, undo and empty-mark cleanup pass on `m4-vi`. Chinese/Korean
IMEs remain unvalidated. See Apple's
[`NSTextInputClient`](https://developer.apple.com/documentation/appkit/nstextinputclient).

`NativeIMESupported` reports whether the platform adapter is attached, not whether
a particular language's input method is installed. `NativeInputError` exposes the
last native callback exception on every platform; callbacks catch exceptions so
they cannot unwind through GTK/GLib, USER32 or AppKit. GTK signal handlers are
disconnected before native controllers/context are released, and stale sources
are rejected before looking up application state. Inspect this property when diagnosing a custom
document handler. Call `CloseInputMethod()` before destroying native widgets on
all three platforms. Attachment errors are reported as Buoy exceptions.

**Composition completion policy:** this version cancels pending text on a click,
focus loss, or editing/navigation command, including on Linux and macOS. It does
not request native completion first. This can discard unfinished input and differs
from standard native text controls; use it only if that cancellation policy is
acceptable. Changing the policy requires real input-method testing, particularly
around asynchronous result notifications. Escape explicitly cancels on all platforms.

This version is intended for small plain-text controls. The demo has no word
wrapping, word movement, blinking/focus-sensitive caret, rich-text layout, context
menu or accessibility text interface. Prefix-width hit testing is suitable for
simple left-to-right text; it is not a bidirectional shaping engine. Movement and
deletion operate on codepoints rather than grapheme clusters (combining characters
and joined emoji may take multiple steps). Long lines incur repeated prefix
measurements and full-document undo snapshots. The demo renders preedit as an
overlay with a uniform underline; it does not lay out a fully reflowed marked-text
document. Full upstream parity still requires a shaped, accessible text-layout
layer and broader native input-method testing.
