# Patched `pdf` package for Object2D paths and alpha

Buoy 0.72.0's stock `pdf-2.4.6.buipkg` (libharu 2.4.6) has two defects that
affect `IGraphics` drawing, including the [Object2D library](../object2d/README.md):

- **Every path paint fails.** `FillPath`/`StrokePath` select colour and line
  width after `MoveTo`/`LineTo`, while libharu is in path-object mode. libharu
  rejects this with error 4177 (`HPDF_PAGE_INVALID_GMODE`), and the page stays
  stuck in path mode, so later calls fail too. `BeginPath` was a no-op.
- **Colour alpha is dropped.** Only R, G and B reach libharu.

This directory builds an opt-in, locally patched package from the stock
archive. The core Object2D module still needs no package; install this only
for projects that draw to `PDFGraphics`. The installed
`/usr/share/buoy/packages/pdf-2.4.6.buipkg` is never modified, and no package
binary is stored in this repository.

## Install

Requirements: Python 3, Buoy 0.72.0 (`buoy pkg seal`) and `llvm-dlltool`
(LLVM 15 or later; Debian's `llvm-19` provides
`/usr/lib/llvm-19/bin/llvm-dlltool`, which is found automatically).

```sh
mkdir -p packages
python3 -I containers/integrations/pdf-patch/build-pdf-package.py \
    /usr/share/buoy/packages/pdf-2.4.6.buipkg packages/pdf-2.4.6.buipkg
```

Put the output in the consuming project's `packages/` directory, replacing
any stock copy there. Programs keep `Package PDF`, and the API is unchanged.
To undo the patch, copy the stock archive back. Repeated builds with the same
Buoy and LLVM toolchain are byte-identical across host time zones: the seal
subprocess runs in UTC. The script prints the resulting
package digest and SHA-256. These can differ between LLVM versions because
`llvm-dlltool` generates different import-library bytes; the source patch and
runtime code stay the same. Both LLVM 18 and LLVM 19 outputs were checked.
The script prefers `/usr/bin/buoy` over this workspace's `/usr/local/bin/buoy`
wrapper, which passes compile flags that `buoy pkg` rejects; use `--buoy` to choose another compiler.

## What the script does

1. Checks the stock archive's SHA-256
   (`0146c952…a6a00cccb`) and the pinned hashes of `modules/PDF.bui` and
   both Windows `pdf.dll`/`pdf.lib` files, then extracts it safely.
2. Applies [PDF.bui.patch](PDF.bui.patch) with exact context and no fuzz.
3. Adds `HPDF_CreateExtGState`, `HPDF_ExtGState_SetAlphaFill`,
   `HPDF_ExtGState_SetAlphaStroke` and `HPDF_Page_SetExtGState` to the export
   tables of both Windows DLLs (x64 and ARM64). The functions are already
   compiled into those DLLs but unexported; Linux `.so` and macOS `.dylib`
   already export them. Their addresses come from each DLL's own COFF symbol
   table (external, function type, executable section). The script writes a
   new `.edata` section, keeping all 42 original exports and ordinals and
   adding ordinals 43–46. No code bytes change, and unsigned DLLs only are accepted.
4. Regenerates `link/<windows triple>/pdf.lib` with `llvm-dlltool`.
5. Removes `files`, `digest`, `platforms` and `modules` from the manifest,
   marks the description as a local patch, fixes timestamps, and runs
   `buoy pkg seal`. Seal recomputes every per-file xxh64 hash and the package digest.
   It reproduces the stock digest exactly when given the unmodified tree.

Linux and macOS native libraries are copied unchanged.

## Behavior of the patched `PDFGraphics`

- **Paths are recorded** by `BeginPath`, `MoveTo`, `LineTo`, `CurveTo` and
  `ClosePath`, then emitted only after colour, alpha and line width are
  selected. This matches native `Graphics`, as measured on Linux/Cairo:
  `BeginPath` discards an unpainted path; `FillPath`/`StrokePath` consume
  the path; points are transformed by the CTM current when they are added;
  the path survives `Save`/`Restore`; a `LineTo`/`CurveTo` without a current
  point starts a subpath. Fill uses the nonzero rule. Painting a path is
  skipped when the CTM is singular or a coordinate is non-finite.
- **Alpha.** Each fill (`Fill*`, `FillPath`, `DrawString`) sets PDF `/ca` from the
  colour's `A`, and each stroke (`Stroke*`, `DrawLine`, `StrokePath`) sets
  `/CA`. The other alpha is left unchanged. Opaque paint after translucent paint
  resets to 1. `DrawPicture` uses `/ca = 1` (the picture's own PNG alpha
  still applies). A colour with `A = 0` draws nothing. Alpha is quantized to
  1/10000, and each distinct pair is one cached ExtGState per document.
  Documents with alpha become PDF 1.4. Opaque-only documents get no ExtGState.
- **State.** `Save`/`Restore` also save the wrapper's CTM mirror, alpha
  and line style. An unmatched `Restore` is now a no-op; the stock package throws
  libharu error 4172 and could otherwise lose the page's top-left coordinate flip.
- **FFI types.** `HPDF_REAL` setters are declared `Single` (C `float`),
  never `Double`. `HPDF_STATUS` returns are `UInt32` on Windows and `UInt64`
  elsewhere. The emitted IR confirms `(ptr, float)` on Windows, Linux and macOS.

## Check a patched package

Build the patched archive using the instructions above, place that archive in a
consumer's `packages/` directory, and compile the PDF-producing application.
Keep one PDF archive selected for that consumer. Check the generated PDF with a
reader or rasterizer on the target platform, including path painting, alpha,
state restoration and any text/image operations the application uses.

## Limitations

- Windows ARM64 runtime behavior and Intel macOS runtime behavior need validation
  on their native targets; compiler/IR checks do not establish rendered output.
- libharu permits 28 nested `Save` operations. Deeply nested Object2D group draws
  can throw `PDFException`.
- The patch addresses the described 0.72.0 package behavior. Review its source
  guards against a different SDK before applying it.

## License and attribution

The package and libharu are upstream works. The `pdf` package is part of
Buoy, whose [license](https://github.com/stretched-out-software/buoy-releases/blob/main/LICENSE.md)
restricts redistribution and repackaging without prior written consent, so
build the patched package locally and do not publish it without that consent. libharu
is under its zlib/libpng-style license (see `/usr/share/buoy/docs/documentation/pdf.md`).
This directory contains only the patch (with minimal upstream context lines),
the build script and documentation. The original source headers in
`PDF.bui` are kept, with a "LOCAL PATCH" note added.
