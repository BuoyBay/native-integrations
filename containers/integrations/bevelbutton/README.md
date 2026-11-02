# Canvas-based bevel button

A Canvas-based bevel button with icons, captions, push/toggle/sticky behavior,
menus, split actions, eight bevel shapes, keyboard navigation and appearance
styling. Inspired by [Xojo's DesktopBevelButton](https://documentation.xojo.com/api/user_interface/desktop/desktopbevelbutton.html),
with matching APIs and event conventions. Tested with Buoy **0.72.0**.

Copy the library files `bevelbutton.bui`, `bevelnative.bui`, `bevelkeys.bui` and
`bevelshortcuts.bui` into your project. `Import bevelbutton` for the control;
`Import bevelshortcuts` when window-wide default/cancel/mnemonic routing is
needed. There is no extra package. Native adapters use the platform libraries
already shipped with the Buoy GUI runtime.

[example.bui](example.bui) is the runnable demo. It uses Buoy's declarative
`Window`/`Control` layout and `With` event handlers. A normal subclass with
`Handle Action()` is equally supported. `ParentWindow` supplies the owning
window; no manual back-reference is needed.

## Behavior and events

| Member | Contract |
| --- | --- |
| `ButtonStyle` | `BevelButtonStyle.PushButton`, `ToggleButton`, `StickyButton` |
| `Value` | Persistent selected/depressed state; toggles flip it, sticky buttons set it true |
| `Press()` | Programmatic activation, subject to effective enablement and visibility |
| `PerformClick()` | Hidden test hook with Buoy's native Button spelling; calls `Press()` |
| `Action()` | Main activation event, following Buoy's native `Button` convention |
| `ValueChanged(newValue As Boolean)` | Fires after a user/programmatic activation changes `Value`, before `Action` |
| `Pressed()` | Compatibility event retained from the first integration; fires after `Action` |
| `CancelPress()` | Cancels pending pointer/key activation without changing `Value` |
| `IsPressed` | Effective pressed/selected appearance |
| `FocusReceived()`, `FocusLost()` | Notifications from observed native focus, including window deactivation |
| `Active` | Last observed activity of the owning native window |
| `Close()` | Idempotent early cleanup; cancels presses, stops monitoring and releases native bindings |

Handle either `Action` or `Pressed` for an action; handling both intentionally
receives both notifications. Directly assigning `Value` repaints and notifies
accessibility without raising activation or `ValueChanged` events.

A left press activates only when released inside the same button segment.
Dragging outside cancels the appearance, and re-entering restores it. Crossing
from the main segment to the menu segment does not activate either segment.
Right clicks retain Buoy's inherited contextual-menu mechanism. Round buttons
hit-test their circle rather than the rectangular corner area.

Space/Return activate on release; held-key repeats are coalesced. Escape cancels
a held press. The inherited `TabPressed` event cancels a press and returns False
so Buoy performs its native Tab/Shift+Tab traversal. Use the inherited
`Focusable`, `FocusIndex`, `SetFocus()`, `Enabled` and `Visible` properties.
A nonfocusable button still supports pointer activation.

## Menus

| Member | Contract |
| --- | --- |
| `Menu As ContextMenu` | Buoy's native menu, populated with `MenuItem` objects and `AddItem`/`AddSeparator` |
| `MenuStyle` | `BevelButtonMenuStyle.None`, `Down`, `Right`; controls the indicator and anchor |
| `SplitMenu` | False: the entire button opens the menu. True: main area activates, arrow area opens the menu |
| `ShowMenu() As Boolean` | Opens a nonempty menu on a visible, enabled, attached control; False if suppressed |
| `MenuOpening() As Boolean` | Return True to cancel. Update/replace `Menu` here before it is shown |
| `MenuSelected(item As MenuItem)` | Delivers the original native Buoy item, including its Tag and child identity |

Menu-only activation raises menu events rather than toggling `Value` or raising
`Action`. Split-button menu activation also leaves `Value` unchanged. Down/F4
open a focused button's menu; Right also opens a right-facing menu. Selection
rejects foreign items and disabled branches. A menu may be shared between
buttons; its current popup owner receives the selection.

The native platform provides dismissal and menu navigation. This integration
registers the selection callback through Buoy's UI bridge to work around the
0.72 `ContextMenu.Show` omission, and focuses the first enabled entry in GTK's
popup. BUI-602
contains the exact native Windows reproduction. The Mac bridge acceptance here
is supporting coverage, not an exact unmodified-Mac reproduction of that defect. No replacement `MenuItem` type is introduced. Those ABI details are
isolated in `bevelnative.bui` and need retesting on a Buoy upgrade.

The stock GTK4 ContextMenu still omits submenu parents and ignores menu icons
and native checkmark rendering. Windows/macOS use the stock nested menu support.
This library preserves the Buoy tree and does not flatten or silently substitute
another menu model. Keep essential Linux actions at the top level.

## Drawing and layout

All dimensions and offsets are Buoy graphics points unless explicitly stated.

| Property | Values / behavior |
| --- | --- |
| `Caption` | Unicode caption; `&S` marks a mnemonic, `&&` draws an ampersand |
| `DisplayCaption`, `Mnemonic` | Read-only parsed caption and lowercase mnemonic |
| `Icon As Picture` | Nil for text only; empty Caption gives an icon-only button |
| `IconSize` | Longest icon dimension, default 24; 0 uses natural size; preserves aspect ratio and fits content bounds |
| `CaptionPosition` | `BevelButtonCaptionPosition.RightOfIcon`, `LeftOfIcon`, `AboveIcon`, `BelowIcon`, `Normal` (right), `SystemDirection` |
| `CaptionAlignment` | `BevelButtonCaptionAlignment.Centered`, `Left`, `Right`, `SystemDirection` |
| `IconAlignment` | `BevelButtonIconAlignment.Centered`, `Left`, `Right`, `Top`, `Bottom`, `TopLeft`, `BottomLeft`, `TopRight`, `BottomRight`, `SystemDirection` |
| `CaptionDelta` | Inset from the selected text slot edge; ignored for centered captions |
| `IconDeltaX`, `IconDeltaY` | Inset the combined icon/caption block from an aligned edge; ignored on a centered axis |
| `Padding`, `Gap` | Inner padding and icon/text separation; both default 6 |
| `TextOverflow` | `BevelButtonTextOverflow.Ellipsis` (default) or `Clip`; ellipsis truncates by Unicode codepoint |
| `FontName`, `FontSize` | Native platform font fallback; empty/System/SmallSystem recognized; size 0 uses the integration's default size |
| `FontUnit` | `BevelButtonFontUnit.Point` or `Pixel`; pixel size divides by the owning window's display scale |
| `Bold`, `Italic`, `Underline` | Applied to both text measurement and drawing |
| `BevelStyle` | `BevelButtonBevel.None`, `Small`, `Normal`, `Large`, `Rounded`, `Round`, `LargeRound`, `Disclosure` |
| `Appearance` | `BevelButtonAppearance.System`, `Light`, `Dark`; System follows `System.IsDarkMode` |
| `BackgroundColor`, `TextColor` | Custom colors; assign Nil to restore automatic light/dark colors |
| `HasBackgroundColor` | False ignores a custom face color and uses the automatic palette |
| `Transparent` | Omits the face fill while retaining border/content; useful for transparent bitmap output |
| `AllowAutoDeactivate` | Dims the caption in inactive windows; does not disable focus-loss cancellation |
| `Tooltip` | Real GTK tooltip, Windows tooltip control, or AppKit help tag |

Icon alignment positions the combined content block; caption alignment then
positions text within its available slot. SystemDirection follows native layout
direction. Round draws a circle; LargeRound draws a capsule; Disclosure draws
an arrow which points down while Value is true. Shapes are portable drawings,
not pixel-identical replicas of each OS's Xojo control.

`MeasureLayout(g) As BevelButtonLayout` exposes measured content, text, icon and
menu bounds for custom drawing. `Draw(g)` paints at the graphics origin and
preserves graphics state. Use it with `Picture.Graphics` for bitmap export or
`Graphics.Translate` for placement. The inherited `Canvas.RenderTo(p)` also
uses the same drawing path. Never retain a Paint event's Graphics.

## Focus, shortcuts and accessibility

The control uses Buoy's `Focusable`, `FocusIndex`, `ParentWindow`,
`AccessibleLabel`, `AccessibleHint`, `AccessibleRole.Button`,
`AccessibleHidden` and `NotifyAccessibilityChanged` surfaces. Caption changes
use Buoy's own default-label setter, so explicit accessibility labels stay
sticky, even when set to the previous caption. `AccessibleHint` remains owned
by the application. Set it explicitly for extra screen-reader help.

The installed compiler lacks a Canvas focus-lost event and does not compile
`Window.IsActive` despite that property's presence in the installed docs.
A 50 ms main-thread Buoy `Timer` observes native focus, activity, effective
visibility, enablement and system appearance. It repaints changes and cancels
held presses on focus loss, hide/disable and deactivation. No host callback is
required for that behavior. Notifications have up to one timer period of latency;
a complete focus-out/focus-in transition within that period can be missed.
Timer and menu registries use `Weak` references to avoid ARC cycles.

For window-wide shortcuts, keep a `BevelButtonShortcuts` in a window property,
`Add` every BevelButton in desired precedence order, and `Open(window)` in
Opening. Include ordinary buttons so a focused button keeps its own Return
behavior. `Default` handles Return, `Cancel` handles Escape, and Alt plus the
caption mnemonic activates that button. Native popup menus keep their keys.
Close the router and controls from the window's Closed handler, as the demo
does. Destructors also clean up when objects are released.

The optional router uses a GTK capture controller, a thread-local Windows
message hook scoped to its window, or AppKit's supported local event monitor.
The Mac monitor filters events by the owning window and leaves native menu
tracking alone. It never replaces `NSWindow`'s class or KVO machinery and does
not install a global keyboard monitor. Its copied block follows the
[Clang Apple Blocks ABI](https://clang.llvm.org/docs/Block-ABI-Apple.html).
Buoy 0.72's system stub omits the Blocks copy/release exports; the adapter
resolves them from the already-loaded system runtime. Supplemental reproduction
and the removal rule are recorded under
BUI-006;
that additional-symbol observation remains pending independent review. `LastError` reports errors caught at native
callback boundaries. One router is allowed per window. Applications with their
own key-routing layer may instead call `button.HandleShortcut(e)` directly;
forwarded, already-handled events are ignored. `LastNativeError` on the button
reports native monitoring/tooltip failures.

Accessibility follows the capabilities of the stock Buoy Canvas bridge. GTK
fixes a DrawingArea's role at class creation, so the runtime's role setter is a
no-op there. Full screen-reader Invoke/Toggle actions and native selected-state
providers for custom canvases are not added by this integration. These remain
upstream/runtime work; labels, hints, focus and change notifications should not
be mistaken for a full native accessible-button implementation.
