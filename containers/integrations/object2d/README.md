# Object2D vector shapes

`object2d.bui` is a source module providing retained vector shapes modeled on
Xojo's [Object2D](https://documentation.xojo.com/api/graphics/object2d.html)
classes. Shapes draw through Buoy's `IGraphics` interface
(`/usr/share/buoy/docs/documentation/igraphics.md`), so one scene can be drawn to a `Canvas.Paint` `Graphics`, a
`Picture.Graphics` offscreen context, or a `PDFGraphics` page. No Buoy package
is required for native drawing or retained-picture persistence; `pdf` is
needed only if you draw to PDF.

Copy `object2d.bui` into your project and import it:

```buoy
Import object2d

Class SceneCanvas Inherits Canvas
    Handle Paint(g As Graphics)
        Dim r As New RectShape
        r.X = 100.0
        r.Y = 80.0
        r.Width = 120.0
        r.Height = 60.0
        r.Rotation = 0.3
        r.FillColor = Color.RGB(0.27, 0.51, 0.71)
        r.BorderOpacity = 100.0
        g.DrawObject(r)
    End Handle
End Class
```

[example.bui](example.bui) builds a grouped scene, hit-tests it, and renders it
offscreen to a PNG: `buoy example.bui -o example && ./example out.png`.

## Library instead of built-in members

Xojo has `Graphics.DrawObject` and `Picture.Objects`. This repository packages
the released Buoy 0.72.0 compiler and runtime without their sources, so those
built-in classes cannot be changed. The module offers:

- **`DrawObject(g, shape, dx, dy)`**, declared as a Buoy extension method
  (`extension-methods.md` in the local documentation).
  `g.DrawObject(shape, dx, dy)` also works for any `Graphics`, `IGraphics`, or
  `PDFGraphics`. It is not a member of `Graphics`.
- **`shape.Draw(g, dx, dy)`**, equivalent to `DrawObject`.
- **Retained pictures.** The optional source module
  [vectorpicture.bui](vectorpicture.bui) adds `VectorPicture` with editable
  `Objects`, native raster rendering, and portable scene save/open. See
  [vector picture usage and formats](VECTOR-README.md). It wraps rather than
  modifies native `Picture`; existing native pictures stay raster. Legacy
  EMF/PICT import is not implemented. No FolderItem additions are needed.

`dx` and `dy` default to 0. They offset the whole drawing, as in Xojo.
`Contains` and `Bounds` do not include them.

## Coordinate model

Each object has a local coordinate space with its origin at its anchor `(X, Y)`.
Drawing translates to the anchor, rotates by `Rotation` radians clockwise
(screen y points down), and then scales by `Scale` uniformly. `Scale = 0` or a
non-finite position or angle draws nothing and hits nothing.

| Class | Anchor `(X, Y)` and geometry |
| --- | --- |
| `RectShape` | Center of a `Width` × `Height` rectangle (default 100 × 100). A single zero dimension draws only its border as a line; both zero draw nothing |
| `RoundRectShape` | Center. `CornerWidth`/`CornerHeight` are the corner oval's full width and height (default 10). They are clamped to the size |
| `OvalShape` | Center of the ellipse inscribed in `Width` × `Height` |
| `ArcShape` | Center. Radii are `Width/2` and `Height/2` |
| `PixmapShape` | Center of the picture, scaled to `Width` × `Height` |
| `TextShape` | Horizontal center and first baseline by default (see below) |
| `CurveShape` | Start point. `X2`/`Y2` and control points are in the same parent space |
| `FigureShape` | Origin of its curves' coordinates. Rotation and scale pivot here |
| `Group2D` | Origin of the children's space. With default X/Y/Rotation/Scale, children draw at their own coordinates |

Xojo describes `X`/`Y` only as "the center or main anchor point". This table
records the choices made where its documentation is silent.

## Shared Object2D members

| Member | Behavior |
| --- | --- |
| `X`, `Y`, `Rotation`, `Scale` | Placement as above. Defaults are 0, 0, 0, 1 |
| `FillColor`, `BorderColor` | Default `Color.Black`. A `Nil` color is not drawn |
| `FillOpacity`, `BorderOpacity` | Percent from 0 to 100, clamped on assignment. They multiply the color's own alpha and are drawn through `Color.RGBA` |
| `BorderWidth` | Points before `Scale`, default 1. Negative or NaN becomes 0 |
| `Draw(g, dx = 0, dy = 0)` | Draws inside `Save`/`Restore`, with `Try`/`Finally` |
| `Contains(x, y)` | Hit test in the parent space (see accuracy notes) |
| `Bounds() As Rect` | Axis-aligned geometric bounds in the parent space, after rotation and scale. Borders are excluded. An empty object returns a zero-size `Rect` at `(X, Y)` |
| `LocalTransform()` | The placement as an `Object2DTransform` affine matrix |

`BorderOpacity` defaults to 0 for `RectShape`, `RoundRectShape`, `OvalShape`,
`ArcShape`, `FigureShape`, and `PixmapShape`, following Xojo's examples. They
set `BorderOpacity = 100` to add a border, and ArcShape documents 0
explicitly. `CurveShape` defaults to 100, because a curve is all border.
`FillOpacity` defaults to 100. Xojo says partial opacity works only on macOS
and Windows. Here it is passed as color alpha, which native `Graphics`
honors on Linux, Windows, and macOS. Stock `PDFGraphics` drops alpha; the
opt-in [PDF patch](../pdf-patch/README.md) applies fill `/ca` and stroke `/CA`
transparency (see the backend notes below).

## Shapes

- **`ArcShape`** (`Inherits OvalShape`) has `StartAngle` and `ArcAngle` in
  radians. 0 is due east, and positive angles run clockwise. A negative
  `ArcAngle` sweeps counterclockwise, and `|ArcAngle| ≥ 2π` is a full ellipse.
  Angles are parametric ellipse angles, which are polar angles only for a
  circle. The fill is a pie wedge to the center, and the border outlines the
  same wedge.
- **`OvalShape`/`RoundRectShape`/`ArcShape.Segments`**: 0 uses native ovals
  and Bézier curves. For ovals, N > 0 draws a polygon with at least three sides. Arcs use
  N subdivisions along their sweep. For round rectangles, N is a corner
  subdivision budget: each corner uses `max(1, N \ 4)` segments, in addition
  to the four straight edges (N = 4 produces an octagon).
- **`CurveShape`** draws from `X, Y` to `X2, Y2`. `X2`/`Y2` default to 100,
  which is Xojo's "X + 100" for the default X = 0. `Order` is 0 for a line,
  1 for a quadratic curve, and 2 for a cubic curve. Other values throw
  `OutOfBoundsException`. `ControlX(i)`/`ControlY(i)` take i = 0..1 and work
  with `Assigns`, for example `c.ControlX(0) = 120.0`. Only the border is
  drawn. `Segments` > 0 draws N straight segments. `New CurveShape(x1, y1, x2, y2)`
  creates a line.
- **`FigureShape`** joins its curves in order. If a curve does not start where
  the previous one ended, a straight line joins them. The last curve is joined
  back to the first, so a figure is always closed. Xojo's two-line triangle
  example fills as a triangle. It provides `AddLine`, `AddQuad`, `AddCubic`
  (`x, y, x2, y2, cx, cy[, cx2, cy2]`), `AddCurve`, `AddCurveAt`, `CurveAt(i)`
  with get and `Assigns`, the `ValueAt` alias, `RemoveCurve`,
  `RemoveCurveAt`, `RemoveAllCurves`, and read-only `Count`. Member curves
  provide geometry only. Their colors, `Rotation`, and `Scale` are ignored,
  but their `Order`, control points, and `Segments` are used. Curves are held
  by reference.
- **`PixmapShape`** (`Inherits RectShape`) has `Image`, `New PixmapShape(picture)`,
  `SourceLeft`, `SourceTop`, `SourceWidth`, and `SourceHeight`. Assigning
  `Image` resets the source region and `Width`/`Height` to the picture's pixel
  size. A partial source region is copied through
  `GetBacking`/`Picture.FromBuffer` on each draw, with source offsets floored
  to whole pixels, so edits through `Image.Graphics` stay visible. Pixels
  outside the image are transparent. Crops are limited to 16 million pixels
  and 32767 pixels per side; larger requests throw `InvalidArgumentException`. Fill and
  border properties are not drawn.
- **`Group2D`** keeps an ordered list and draws first to last. It provides
  `AddObject`/`Add`, `AddObjectAt`/`Insert` (index 0..Count),
  `Item(i)` with get and `Assigns`, `IndexOf`, `RemoveObject`/`Remove`
  (identity, no-op if absent), `RemoveObjectAt`, `RemoveAll`, `Count`,
  `HitTest(x, y)` (topmost direct child or `Nil`), and `Encloses(obj)`.
  Adding or assigning `Nil` throws `NilObjectException`. Adding a group that
  already contains this group, directly or through nested groups, throws
  `InvalidArgumentException`. Enclosure/cycle checks visit each distinct group
  once, so repeated references to shared subgroups do not expand every path. The same object may appear in several groups.
  Rendering, `Contains`, `Bounds`, and cycle checks stop with
  `UnsupportedOperationException` beyond 256 nested levels. The group's own
  fill and border properties are not applied to its children.

## TextShape

This follows Xojo's [TextShape](https://documentation.xojo.com/api/graphics/textshape.html)
members: `Text`, `FontName`, `FontSize`, `Bold`, `Italic`, `Underline`,
`FillColor`/`FillOpacity` for the text color, and `HorizontalAlignment`/
`VerticalAlignment` of type `TextShape.Alignment`
(`Left = 0, Top = 1, Center = 2, Baseline = 3, Right = 4, Bottom = 5`).
`StringShape` is a legacy alias subclass. Border properties are ignored.
`FontUnit` supports `FontUnits.Default`, `Pixel`, `Point`, `Inches`, and
`Millimeter` (values 0..4). The default is `Point` to preserve the library's
existing behavior. Inches convert at 72 points/inch; millimeters at 72/25.4.
Pixel sizes divide by the instance's positive `PixelsPerPoint` (default 1).
`IGraphics` exposes no DPI query, so set this for the destination rather than
assuming the primary monitor's DPI. `Default` follows Pixel on Windows and
Point elsewhere; exact Xojo legacy Linux font scaling is not reproduced.
A size of zero selects `DefaultFontSize` in points regardless of `FontUnit`.

- **Defaults.** Horizontal is `Center` on `X`, and vertical is `Baseline`
  on `Y`, with `FontName = "System"` and `FontSize = 0`. "System",
  "SmallSystem", and an empty name map to the shared `TextShape.SystemFontName`
  (Helvetica on macOS, Segoe UI on Windows, and Sans on Linux). A size of 0 or
  less uses `TextShape.DefaultFontSize` (12). For PDF, set a base-14 or loaded
  font such as "Helvetica".
- **Alignment.** Horizontal values other than `Left`/`Right` act as `Center`.
  Vertical `Top` puts the block's top at `Y`. `Center` centers the block, and
  `Bottom` puts its bottom at `Y`. Other values, including the default, place
  the first baseline at `Y`.
- **Multiline.** Xojo's page says both to "use a carriage return" for
  multiple lines and that line breaks are "not supported". This module
  supports them: CR, LF, and CRLF start a new line. Each line is aligned
  separately and advances by `MeasureStringHeight("Xg") × TextShape.LineSpacing`.
  The ascent used for Top, Center, and Bottom is `TextShape.AscentRatio`
  (0.8) of that height, an approximation because `IGraphics` has no font
  metrics. There is no word wrapping.
- **Styles.** `IGraphics` has no font-style members, but native `Graphics`
  has `Bold`/`Italic`/`Underline`. When the target is a `Graphics`, the shape
  saves those three values, applies its own, and restores them in `Finally`.
  `Graphics.Save`/`Restore` is not documented to cover font style. On other
  backends such as `PDFGraphics`, `Underline` is emulated with a line below
  each baseline, and `Bold`/`Italic` have no effect.
- **Measurement.** `Contains` and `Bounds` need text metrics, but they have no
  graphics context. Drawing caches the measured layout box. You can also
  call `shape.Measure(g)` first. Until then, a box is estimated at 0.55 em
  per character and 1.2 em per line. `IsMeasured()` reports whether the cache
  matches the current text, font, style, and alignment. `LayoutBox()` returns
  the local box.

## Hit testing and bounds accuracy

- Rectangles, ovals, round rectangles, and arcs (with `Segments = 0`) use
  exact geometric tests. With `Segments` set, the drawn polygon is tested
  instead.
- Curves and figures are flattened into polylines, with 64 segments per curve
  (or `Segments` if set). `FigureShape.Contains` uses the even-odd rule on the
  flattened outline, which matches native filling for figures that do not
  intersect themselves. Near the edge of a degenerate figure, it also counts
  points within the border.
- `CurveShape.Contains` is true within `max(1, BorderWidth / 2)` local units
  of the flattened curve.
- `Bounds` solves extrema after the complete group transform: analytic
  ellipse/arc extrema and derivative roots for quadratic/cubic curves,
  figure edges, and rounded-rectangle corner Beziers. It no longer samples
  smooth geometry. Explicit polygon `Segments` bounds the actual polygon.
  Borders are excluded. These are geometric bounds; antialias fringes and
  native ellipse-to-Bezier rasterization can extend pixels slightly past them.
- `PixmapShape` tests its whole rectangle, ignoring transparent pixels.

## Platform and backend notes

Object2D draws through Buoy's platform graphics backend. GUI-enabled Linux
consumers need the matching image runtime, including a genuine JPEG ABI-8 library
where required by the installed Buoy runtime.

On Windows, Buoy 0.72.0 uses GDI text/picture operations alongside GDI+ transforms.
`TextShape` and `PixmapShape` compensate by transforming a transparent raster
before blitting. Translation, rotation, uniform/negative scale and nested groups
are supported by that fallback. Sampling is nearest-neighbor and text is rasterized
at its original font size, so enlargement is less smooth than vector text.
Intermediate rasters are limited to 16 million pixels and 32767 pixels per side;
larger requests throw `InvalidArgumentException`.

Caller-applied transforms/clips before `DrawObject` cannot be recovered through
`IGraphics` by this Windows fallback. Express placement through shapes/groups
and drawing offsets. Native multiline text spacing can differ between backends.
Recheck `Object2DNeedsDeviceSpace` when adopting a runtime that changes these
Windows graphics operations.

For PDF path drawing/transparency with the affected Buoy 0.72.0 SDK, use the
[PDF compatibility patch](../pdf-patch/README.md) according to its license and
build instructions. The stock package drops color alpha and can fail path painting
with libharu error 4177. Select a PDF font face explicitly for bold/italic;
underline is emulated. libharu permits 28 nested graphics saves, so deeply nested
groups can throw `PDFException`.

## Extending

Custom subclasses in another file can override `DrawLocal(g, depth, device)`
and `LocalContains(lx, ly, depth)`. Override `Outline() As Object2DPolyline`
for polygon hit tests and bounds, or `CollectLocalBounds(m, box, depth)`
using the public `Object2DTransform` and `Object2DBoxBuilder` helpers for
analytic bounds. Custom shapes without any geometry hook have empty bounds.

## Build the example

From the repository root, with the matching Buoy graphics runtime installed:

```sh
mkdir -p dist/object2d
buoy containers/integrations/object2d/example.bui --check --diagnostic-format json
buoy containers/integrations/object2d/example.bui -o dist/object2d/example
```

Run the output with its deployed runtime files on the intended platform.
Validate geometry, text, images and PDF output using the backends your application
uses; compiler success alone does not establish rendering behavior.
