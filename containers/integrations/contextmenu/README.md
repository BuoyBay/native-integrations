# GTK4 contextual menus

`gtkcontextmenu.bui` is a reusable Linux adapter. It uses
GTK4's `GtkPopoverMenu` and GIO actions through `Declare`; it does not modify
the installed compiler or runtime. Nested submenus remain available on Linux.
No additional Buoy package, C shim, or GTK development headers are needed.

Copy the module into your project and `Import gtkcontextmenu`. Run `example.bui`
for a right-click demo with two submenu levels, a disabled command, a checkmark,
an icon, and contents rebuilt on every request.

## API

- `PopupItem(caption, tag)` holds `Caption`, string `Tag`, `Enabled`, `Checked`,
  `Checkable`, `IconName`, and `IconFile`.
- `AddItem(child)`, `AddSeparator()`, `Count()` and `Item(index)` build and inspect
  the tree. A captionless `PopupItem` acts as its root. Separators remain in the
  public tree. Cycles, repeated parenting, and children on separators are rejected.
- `GTKContextMenu.Show(owner As UIControl, location As Point, root As PopupItem)`
  shows the tree at a control-local point. An empty root suppresses the popup.
  Calling `Show` again closes the previous popup owned by that instance.
- Subclass `GTKContextMenu` and handle `Selected(item As PopupItem)`. Selection
  passes the original item, so identity and tags survive dispatch. `example.bui`
  demonstrates wiring this from a control's `ConstructContextualMenu` event.
  Leave the event's built-in `base` empty to suppress Buoy's own menu.
- `Close()` is idempotent. Call it before detaching the owner or destroying its
  window while the menu is open, and before shutting down the event loop.
- `IsOpen` reports whether the native popup session exists. On dismissal it clears
  on the next event-loop idle turn, allowing GTK's pending action to be delivered.
- `LastError` records exceptions thrown by selection handlers instead of allowing
  them to cross a C callback boundary. A subsequent `Show` clears it.

All calls belong on the GUI thread. `Show` returns immediately. Items are a
snapshot at opening: edit state before showing the menu again. `Checkable`
displays an unchecked or checked native checkmark; `Checked = True` also implies
a checkmark. Selection does not automatically change your model's checked state.

## Icons and compatibility

Normal leaf commands display `IconName` from the installed icon theme or
`IconFile` from a filesystem path (`IconFile` takes precedence). These use custom
GTK button content so the icon appears beside the caption. File lookup/decoding
and theme availability follow GTK. Icons on submenu parents and checkable items
are passed to the native menu model and their display depends on GTK styling.
This adapter does not accept Buoy `Picture` objects directly.

The item model is separate from Buoy `MenuItem`: in 0.72.0, `MenuItem.Count()` and
`Item()` do not expose entries added by `AddSeparator`, so converting an existing
tree would lose separator positions. The demo uses Buoy's right-click request
event, but receives selection on the menu adapter rather than the control's
`ContextualMenuAction` event. Automatic Xojo-style parent event propagation,
shortcut registration, and a separate keyboard menu-key trigger are not provided.

The native adapter requires Linux and GTK4. Its public model is portable, but
`Show` throws on other platforms. Use Buoy's built-in contextual menus there.
GTK menus use native keyboard navigation; the adapter requests traditional nested
submenus with `GTK_POPOVER_MENU_NESTED`, available since GTK 4.0.

## Built-in Windows/macOS verification

The separate `native-fixture.bui` exercises Buoy’s built-in menu runtime without
importing this GTK adapter. See native validation for the
fixture, platform evidence, and the distinction between native model checks and
visible popup/input testing.
