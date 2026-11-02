# Retained vector pictures

Import `object2d` and `vectorpicture` to keep an editable scene separate from
Buoy's native raster `Picture`. `VectorPicture.Objects` is a real `Group2D`:
changes to its shapes appear on the next draw or render. The native `Picture`
class cannot acquire an `Objects` property through Buoy's extension mechanism.

```buoy
Import object2d
Import vectorpicture

Sub SaveScene(file As FileSystemItem)
    Dim scene As New VectorPicture(320, 200)
    Dim box As New RectShape
    box.X = 160.0
    box.Y = 100.0
    box.FillColor = Color.Blue
    scene.Objects.AddObject(box)
    scene.Save(file)
End Sub
```

`VectorPicture.Open(file)` and `Picture.OpenVector(file)` both return a
**VectorPicture**, not a native Picture. They read the versioned buoy-vector
JSON format described below. `OpenVectorPicture(file)` is the equivalent
free function. The `Picture.OpenVector` spelling is a Shared extension.
No `FolderItem` implementation or extension is involved.

Xojo's current `Picture.OpenVector` reads legacy platform vector files
(PICT/EMF). These extensions do **not** implement PICT, EMF, arbitrary SVG,
or PDF import. SVG output can be rasterized with Buoy's existing
`Picture.FromSVG`; that operation does not recover editable shapes.

## API

| Member | Behavior |
| --- | --- |
| `New VectorPicture(width, height)` | Positive pixel dimensions; transparent canvas |
| `Width`, `Height` | Read-only dimensions |
| `Objects As Group2D` | Editable retained scene, initialized empty |
| `Draw(g As IGraphics, dx = 0, dy = 0)` | Draws the retained scene into a Canvas, Picture, PDF, or other backend |
| `Render() As Picture` | Draws into a fresh transparent native raster Picture |
| `ToJSON() As String` | Encodes the full editable scene as buoy-vector version 1 |
| `FromJSON(source) As VectorPicture` | Shared factory; validates and restores the scene |
| `Save(file)` / `Open(file)` | Write/read the editable scene; `.buoyvector` is the suggested extension |
| `ToSVG() As String` / `SaveSVG(file)` | Export a self-contained SVG with vector geometry, styled text and embedded PNG images |

`Save` and `SaveSVG` overwrite the destination after encoding succeeds; a
write failure can leave a partial file. Errors are exceptions:
`InvalidArgumentException` for invalid data/limits, `JSONException` for
invalid JSON syntax, `UnsupportedOperationException` for unsupported shape
kinds, `NilObjectException` for missing objects/arguments, and `IOException`
for file failures. Imports fail as a whole instead of skipping bad shapes.
Rendering retains the native backend limitations documented in the main
[Object2D README](README.md).

## Editable scene format

The UTF-8 JSON document has `format: "buoy-vector"`, `version: 1`, canvas
`width`/`height`, and an `objects` root of kind `Group2D`. Each shape records
its concrete kind, placement, colors and styling plus its geometry. All built-in
library shapes are supported, including `StringShape`, quadratic/cubic control
points, figure curve lists, arc angles, segment counts, nested groups,
multiline text and font units. Images store raw straight-alpha RGBA pixels as
Base64, retaining their source rectangle and destination dimensions.

The importer requires correctly typed fields and validates ranges, finite
numbers, supported versions, image byte lengths and Base64 before creating
pixel buffers. Missing or wrong-type fields are rejected rather than silently
coerced. Extra object fields are currently ignored. Runtime custom subclasses
are rejected by their concrete type name instead of being serialized as a
base class with lost semantics. The document is a scene tree: repeated
references to the same shape/image are encoded independently and restored
as independent objects. Object identity sharing is not retained.

Raster bytes round-trip exactly for opaque pixels. Partially transparent RGB
channels can differ slightly because native Picture storage premultiplies
alpha; see Buoy's raw Picture pixel documentation. Font family metafonts
remain metafonts, and global `TextShape` font/layout defaults are not embedded;
rendering can therefore differ across machines and installed fonts.

Bounds on scene persistence/rendering are deliberate:

- At most 32 MiB of encoded JSON or SVG; 16 MiB of text/font strings while encoding JSON.
- At most 10,000 shapes, counting figure curves and duplicated references.
- At most 64 nested shape levels. JSON nesting is bounded before calling the parser.
- At most 4,194,304 pixels in the canvas and separately across all embedded image copies, with a maximum of 32767 pixels per side.
- Persisted segment counts are integers from -100000 through 100000. Nonpositive values retain the core library's native-curve behavior.

SVG export preserves shape placement, nested groups, colors/alpha, borders,
curved paths and explicit polygon approximations. Text is measured with a
native offscreen Graphics so exported baseline placement follows the current
platform's metrics, then emitted as editable SVG text. Bold, italic, underline
and XML escaping are preserved; the viewing machine must have a suitable font.
Images are cropped through `PixmapShape.SourcePicture` and embedded as PNG.
The exporter caps explicit subdivisions at 4096 per curve/arc (per corner for
round rectangles) and rejects XML control characters instead of producing
invalid SVG. It does not export inherited caller graphics state such as
clipping, dash patterns, or transforms outside the scene.
