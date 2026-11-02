# Canvas- and View-based native controls — Cocoa, GTK, Win32

This collection adds reusable Canvas- and View-based controls and desktop adapters built on Cocoa,
GTK and Win32 APIs. Use them when an application needs native behavior beyond
a built-in control, while retaining the platform's editing and event model.

## Components

- [SearchField](containers/integrations/searchfield/README.md): native search entry,
  live edits, commit/cancel actions and clear behavior.
- [TreeView](containers/integrations/treeview/README.md): native hierarchical display.
- [SegmentedButton](containers/integrations/segmentedbutton/README.md): segmented selection.
- `textinput/`: native text input, IME transport and text-model adapters.
- `contextmenu/`, `printing/`, `popover/` and platform-specific modules provide
  additional focused integrations.

## Try a control

With the compatible Buoy compiler installed:

```sh
mkdir -p dist/searchfield
buoy containers/integrations/searchfield/example.bui --check --diagnostic-format json
buoy containers/integrations/searchfield/example.bui -o dist/searchfield/demo
```

Run the demo on its supported desktop backend with the compiler's deployed
runtime files. Component guides document source imports, parent attachment,
ownership, events and target-specific behavior. Cross-target compiler checks do
not verify native input, focus, accessibility or lifecycle behavior on another OS.

For Linux UI-bridge lifecycle requirements, use the
[GTK guard](https://github.com/BuoyBay/gtklifecycle) where specified. Native SDKs,
platform libraries and desktop sessions remain requirements of the relevant
component rather than dependencies of every application using this collection.

## Local Buoy setup

On your own machine, install Buoy and run:

```sh
buoy ai init --both
```

[Contributing](CONTRIBUTING.md) · [License](LICENSE)
