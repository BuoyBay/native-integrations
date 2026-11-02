# Windows native printing

Import `WinPrinting` (optionally `As PrintInterop`) from the Windows integration
directory. Preserve the sibling `printing/printingtypes.bui` shared-type module,
which the backend imports by relative path; copying only `WinPrinting.bui` is
insufficient. The cross-platform facade handles these imports for applications.
This backend shares its function contract with the Linux CUPS backend. It uses
Windows printer discovery and GDI rendering through the selected printer driver.
No helper DLL, shell command, PDF viewer, or raw printer-language support is required.
Deploy the compiler's complete output directory with its runtime DLLs.

| API | Behavior |
| --- | --- |
| `IsSupported()` | True for Windows; safe on other platforms. |
| `IsAvailable()` | Whether GDI and the Windows spooler library load. Does not test service health, permissions, printer presence or readiness. |
| `Printers()` | Owned `WindowsPrinterInfo` records with `Name` and `IsDefault`; local printers and the user's established remote connections. |
| `DefaultPrinter()` | `Optional Of String`; `None` if the user has no configured default. |
| `PrintText(printerName, title, text)` | Explicitly submits a Unicode text document to the named printer. Returns a positive Windows spool job ID. |
| `PrintPages(printerName, title, document)` | Submits shared `BuoyPrintDocument` pages containing baseline-positioned text runs. |

`PrintText` never implicitly selects the default printer. Printer name and title
must be nonempty. All inputs are limited to 1 MiB of UTF-8 each and checked for
zero bytes. Buoy 0.72 currently truncates strings at NUL and `String.Chr(0)` is
empty; validation cannot recover content already removed by the language runtime.
All native operations throw `UnsupportedOperationException` on other targets.

Printing is synchronous and can block on the driver, spooler or network. Run it
away from the GUI thread. A returned job ID means Windows accepted the document;
it does not establish that physical output completed. File-output printers can
display their own destination dialog. The API does not provide silent PDF output,
printer setup dialogs, cancellation/status tracking, duplex/copy settings or a
complete graphics canvas. Driver/user defaults determine paper and orientation.

`PrintPages` supports the Xojo-inspired text display list used by the shared
facade. Coordinates and font sizes are points (72/inch), `Y` is the text baseline,
and the origin is the physical paper's top-left corner. Hardware margins are
subtracted when mapping to the printer DC. Each explicit page is clipped to
both its logical canvas and the driver's printable surface. **PageWidth and
PageHeight do not negotiate printer media or orientation.** The driver/user's
actual paper setting remains unchanged, with no implicit scaling; content can
be clipped if that paper differs from the logical canvas.

The display-list limits are 1..14400 points per page dimension, 1..1000 pages,
100000 text runs and 16 MiB total UTF-8 content. Coordinates must be finite and
inside the logical page; font sizes are 1..1000 points. Runs are single-line,
without tabs. Native face names are limited to 31 UTF-16 units. `System`,
`SmallSystem` and `sans-serif` map to Segoe UI; `serif` maps to Times New Roman,
and `monospace` to Consolas. Other names use the GDI font mapper. The backend
does not wrap or paginate a display-list run: the facade controls page breaks.

## Text layout

GDI selects 12-point Segoe UI (or the font mapper's substitute), black text on a
white background, with half-inch margins inside the driver's printable area.
CRLF and lone CR normalize to LF; tabs become four spaces. Each logical line is
hard-wrapped using the printer's measured text extents and automatically paginated.
UTF-16 surrogate pairs are kept together at wrapping boundaries. Measurements are
bounded to 4096 UTF-16 units at a time; the document stops at 10000 pages. Empty
text produces a blank page. A character wider than the printable area raises an
error rather than silently clipping it.

This is basic plain-text output: complex-script shaping, grapheme-aware wrapping,
bidirectional paragraph layout, font embedding, rich text, images and matching
pagination across OS backends are outside this interface. Installed fonts and the
printer driver determine glyph coverage. A native failure aborts an active job
before releasing the font and device context. Abort cannot retract pages that a
printer already produced.

## Native ABI and loading

Supports x86-64 and ARM64 Windows with Buoy 0.72. The native structures match
`PRINTER_INFO_4W` (24 bytes/alignment 8), `DOCINFOW` (40 bytes/alignment 8), and
`SIZE` (8 bytes). Enumeration buffers and text copies are owned by Buoy; native
printer handles do not escape. The font is deselected before deletion, the DC is
released in `Finally`, and `AbortDoc` runs if an active job fails.

Buoy's optional-library loader appends `.dll` to names that do not end in `.dll`,
so `Optional Declare Lib "winspool.drv"` would attempt the wrong filename.
The backend obtains the Windows system directory, loads its exact `winspool.drv`
with `LoadLibraryExW` restricted to that directory/System32, resolves documented
typed function pointers, and releases the library in `Finally`. GDI functions use
ordinary `Optional Declare Lib "gdi32"`. These load flags require Windows 8 or
the corresponding Windows 7 loader update; Buoy's own runtime requirements apply.
