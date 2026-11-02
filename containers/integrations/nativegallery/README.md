# Native desktop controls

A source-level native control collection, with a single
[gallery application](main.bui). It uses AppKit on macOS, GTK4 on Linux, and
Win32 controls/windows on Windows. No HTML renderer, Canvas painting, WinUI,
or Libadwaita runtime is introduced.

The gallery imports the modules together and demonstrates search, segmented
selection, project navigation, scrolling native child controls, numeric input,
activity animation, tooltips, arbitrary-content popovers, and color/font dialogs.
The color and font pickers update the gallery heading.

## Components

- [SearchField](../searchfield/README.md): `NSSearchField`, `GtkSearchEntry`,
  or a native Win32 EDIT with a Clear button. Live change, commit and cancel events.
- [ScrollView](../scrollview/README.md): owned Buoy content View inside
  `NSScrollView`, `GtkScrolledWindow`, or a Win32 scrolling container.
- [TreeView](../treeview/README.md): stable `TreeNode` objects backed by
  `NSOutlineView`, GTK4 tree-list/expander widgets, or `SysTreeView32`.
- [NativePopover](../popover/README.md): owned native content, anchored to a
  control, backed by `NSPopover`, `GtkPopover`, or a Win32 popup window.
- [NumberBox](../numberbox/README.md): validated numeric editing composed from
  Buoy's native TextField and Stepper, with bounds and fractional stepping.
- [ColorPicker](../colorpicker/README.md): `NSColorPanel`, `GtkColorDialog`,
  or `ChooseColorW`. Windows selection is opaque; check `SupportsAlpha`.
- [FontPicker](../fontpicker/README.md): AppKit font panel/manager,
  `GtkFontDialog`, or `ChooseFontW`.
- [NativeSeparator and ActivityIndicator](../nativeindicators/README.md):
  native separators plus AppKit/GTK spinners or a Win32 marquee progress bar.
  Windows Common-Controls v6 is activated through a private temporary manifest;
  consumers do not need to deploy a separate manifest file.
- [NativeTooltip](../tooltip/README.md): native hover help on a `UIControl`,
  with weak managed ownership and restoration of an earlier tooltip.
- [SegmentedButton](../segmentedbutton/README.md): existing native control,
  now hardened against obsolete callbacks and destroyed Windows parents.

These are native primitives and native compositions. They preserve platform
behavior rather than imposing one visual style. In particular, AppKit's color
and font panels are modeless/live, while the Windows pickers are modal dialogs
and GTK uses asynchronous dialogs. The component APIs expose those differences.

## Build and run

From the repository root, with Buoy and the selected desktop runtime installed:

```sh
mkdir -p dist/native-gallery
buoy containers/integrations/nativegallery/main.bui --check --diagnostic-format json
buoy containers/integrations/nativegallery/main.bui -o dist/native-gallery/gallery
./dist/native-gallery/gallery
```

The executable also accepts `--smoke` for its built-in initialization/readback
check. Run interactive behavior on a supported desktop session. Keep the entire
deployment directory together, including compiler-deployed runtime libraries.
Linux applications need the matching GTK and image runtime libraries. Windows
applications need a usable interactive desktop for native dialogs and input.

## Lifecycle and integration

Most View-hosted controls use an explicit `Open()` after attachment, normally
in the owning window's `Opening` event. Populate owned content before opening
its native host. Call `RefreshNative()` after host geometry/enablement changes,
and `Close()` during the owning window's `Closed` event. The gallery shows this
ordering; each component README documents exceptions such as terminal popover
closure and asynchronous picker cancellation.

The components do not need global keyboard hooks or polling timers. Native
callback bridges contain exceptions rather than unwinding into OS code;
`LastNativeError` reports captured failures. Programmatic property assignment
is generally silent; activation/commit methods have explicit event contracts.

Buoy currently shares generated Optional Declare wrappers by library+symbol
across modules. The collection therefore uses consistent Win32
`SendMessageW`/`DefSubclassProc` signatures (`LPARAM As Int64`). Mixing another
binding with a conflicting signature can pass semantic checks and fail LLVM
verification; the combined gallery build tests this integration boundary.

## Platform requirements and limits

Color/font dialogs need GTK 4.10+; TreeView keyboard-focus behavior needs GTK
4.12+. These wrappers use the native controls rather than substituting a custom
renderer when a platform prerequisite is unavailable.

Exercise keyboard/mouse input, accessibility, IME, wheel/trackpad behavior and
mixed-monitor DPI on the target desktop. A successful cross-target compiler check
does not establish those native behaviors. Programmatic smoke mode covers a
smaller initialization/readback contract than an interactive gallery session.

Suggestions/history in SearchField, large-tree lazy loading, unified numeric
accessibility, automatic focus-to-visible scrolling and complete designer/runtime
integration remain extension work.
