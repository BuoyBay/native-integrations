# View-based native TreeView / OutlineView

A reusable View-based tree control with stable `TreeNode` identity, native
selection, disclosure controls, scrolling, and keyboard navigation. It hosts
native controls in a `View`; no Canvas, HTML, custom painting, deprecated
GTK TreeView, or WinUI hosting is used.

- **macOS:** AppKit `NSOutlineView` inside `NSScrollView`, with a native
  Objective-C data source/delegate implemented through Buoy FFI callbacks.
- **Linux:** GTK4 `GtkTreeListModel`, `GtkSingleSelection`, `GtkListView`, and
  `GtkTreeExpander` inside `GtkScrolledWindow`. Requires **GTK 4.12 or newer**
  for the list-item focus setting used by native tree keyboard bindings.
- **Windows:** common-controls `SysTreeView32`, with native tree items and
  selection/expansion notifications. The Windows adapter invalidates handles
  on native destruction to avoid accessing recycled HWNDs.

## Use

Copy [treeview.bui](treeview.bui) into a project and `Import treeview`.
[example.bui](example.bui) is a runnable declarative-window demo containing a
nested project tree and a `With … Handle SelectionChanged(node As TreeNode)`
handler. There is no additional package or compiled shim.

Populate nodes, add the control to its window/container, and call `Open()` from
the window's `Opening` handler. Buoy creates Windows container HWNDs lazily, so
attachment must precede `Open`. Call `RefreshNative()` after geometry changes
through `Move` or constraints. Call `Close()` from the window's `Closed`
handler. Cleanup is idempotent and the destructor also cleans up.

A normally closed tree can be opened again. After an externally destroyed
Windows native container/control, create a new TreeView; re-opening the old
Buoy object is rejected because its inherited native handle may be stale.

## Model and selection

- `New TreeNode(caption)` creates a node. `Caption` and string `Tag` are mutable.
- `AddChild(node)`, `RemoveChild(node)`, `ChildCount`, `ChildAt(index)` manage
  immediate children. `ParentNode`, `OwnerTree`, and `Contains(node)` inspect
  membership. Nil children, cycles, and duplicate ownership are rejected.
- `TreeView.AddRoot(node)`, `RemoveRoot(node)`, `Clear()`, `RootCount`, and
  `RootAt(index)` manage roots. Detach a node before adding it elsewhere.
- `SelectedNode` is the original `TreeNode`, or Nil. Assignments are silent;
  selecting a nested node expands its ancestors. Foreign nodes are rejected.
- `SelectionChanged(node)` reports native user selection changes. A selection
  cleared by the native control may report Nil. Handler exceptions are caught
  at the native boundary and recorded in `LastNativeError`.
- Set `node.Expanded` before opening for an initial expanded state. After
  opening, use `SetExpanded(node, expanded)` and `IsExpanded(node)`. These
  update/query the native control, and native expansion updates model state.
- Node caption/child/root mutations call `Reload()` automatically. Reloading
  preserves node identity, expansion state, and the selected node if it still
  belongs to the tree. Removing the selected node clears selection.

`AttachTree` is integration plumbing, not an application mutation API; use
`AddRoot` and `AddChild`. All methods belong on the GUI thread.

## Native behavior and first-version limits

`Indentation` controls the logical distance per hierarchy level (0–64, default 16).
`IconSize` controls the logical icon side length (12–48, default 20). The native
row height fits the icon with padding. Both may change after `Open()` and preserve
node identity, expansion, and silent selection. Studio uses 10-point indentation
and 16-point icons; macOS loads the bundled HiDPI artwork into native image cells.

The OS paints rows, focus, disclosure controls, and scrollbars and provides
native accessibility objects. Screen-reader interaction has not been tested.
GTK uses its native TreeExpander shortcuts: `Shift+Left`/`Shift+Right` collapse
and expand, while Up/Down navigate rows. Other platforms retain their native
outline/tree keyboard conventions.

This first version is a single-selection, text-only tree. It eagerly builds
native node models while GTK virtualizes row widgets. Lazy application data
loading, icons, checkboxes, multiple columns, multiselect, drag-and-drop,
and inline rename are not implemented. `ContextRequested(node, location)` selects
the right-clicked row silently and lets the host show a per-node `ContextMenu`.
The event uses control-local coordinates and works on native GTK, AppKit and
Win32 rows; `RequestContext` provides the same entry point for keyboard commands. Structural mutations
rebuild native controls, so scroll position and keyboard focus may reset.
For large imports, construct a detached subtree first and add it in one call.

## Native macOS validation

ARM64 macOS **27.0.1** on `m4-vi`, with Buoy **0.72.0**, passed the native
contract executable with exit 0 and empty stderr. Coverage includes native
NSOutlineView row selection, ancestor expansion/collapse, selection identity
through mutations/reloads, real AppKit selection-notification callbacks,
exception containment and close/reopen cleanup. The demo built as a native
`.app`. Standalone native callbacks were driven programmatically. The combined Mac gallery also passed real pointer selection and keyboard navigation; physical expansion/collapse needs separate coverage. macos-validation.json
records source hashes and execution provenance.

Use `--app-type console` when compiling `smoke.bui` on macOS. The demo uses
`--app-type desktop` and produces an `.app` bundle.

The Windows `lifecycle-smoke.bui` regression measures GDI objects across twenty
external host-destruction cycles. Owned image lists must be released even when
`WM_NCDESTROY` clears the normal lifecycle registry. Build it with the aggregate
runner (`--controls treeview`), then run `lifecycle-smoke.exe` in the Windows lab.
