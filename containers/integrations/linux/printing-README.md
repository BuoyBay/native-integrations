# Linux CUPS printing

Keep `linuxprinting.bui` together with the sibling
`../printing/printingtypes.bui` shared records when copying this integration.
Import the backend with an alias, or use the shared printing facade. The module
implements native CUPS 2 calls and optional Pango/Cairo PDF rendering. No shell
commands or helper processes are used by the module.

| API | Behavior |
| --- | --- |
| `IsSupported()` | True for a Linux target; safe on every platform. |
| `IsAvailable()` | Whether `libcups.so.2` loads. Does not contact a server or establish printer availability. |
| `Printers()` | Owned `LinuxPrinterInfo` objects with `Name` and `IsDefault`. |
| `DefaultPrinter()` | Optional base queue name; `None` when no enumerated destination is default. |
| `PrintText(printerName, title, text)` | Submits UTF-8 `text/plain` to an explicit queue and returns the positive accepted CUPS job ID. |
| `PrintPages(printerName, title, document)` | Shapes the shared text display list with Pango/Cairo, then submits `application/pdf` to the explicit queue. |
| `ExportPDF(fileName, document)` | Uses exactly the same PDF renderer without contacting CUPS. Explicit destination is overwritten; validate inputs before creating it. |

The CUPS server and current user's configuration determine destination discovery
and the default. Named option instances collapse to their base queue; an
instance selected as default marks its base queue default. Instance-specific
options are not inherited by `PrintText`. These synchronous calls can contact a
configured remote CUPS server and can block. Applications should call them away
from the UI thread and handle the server's authentication requirements.

`PrintText` is an explicit side effect. It never silently selects a default
printer. The printer name and title must be nonempty; the body can be empty.
Each input is limited to 16 MiB of UTF-8 and is checked for NUL bytes. Buoy 0.72
already truncates some embedded-NUL strings, so the module cannot recover bytes
lost by the language runtime.

Text is written to a randomly named `mkstemp` file with mode 0600. Writes handle
short writes and `EINTR`; the descriptor closes before CUPS reads it, and native
options and the temporary input are cleaned up in `Finally`. Unlink cleanup is
best effort: an already accepted job is not reported as failed due to a cleanup
error, which could otherwise encourage duplicate submissions.

A returned job ID confirms spool acceptance, not successful physical output.
CUPS applies the queue's configured text filters, fonts, media, banners and job
defaults. A queue that cannot convert `text/plain` can reject the document or
fail later. This backend does not provide a drawing canvas, a print dialog,
pagination control for plain text, or a cross-platform typography guarantee.

`PrintPages` supplies the positioned-text path used by the shared Xojo-style
graphics facade. A document contains explicit pages; each text run specifies
content, font family and size, and baseline X/Y coordinates. Coordinates, font
sizes, and the logical page dimensions use points (72 points per inch).
Each page is emitted with `cairo_show_page`, preserving explicit blank pages.
`System` and `SmallSystem` font names map case-insensitively to `sans-serif`;
the provided `FontSize` remains authoritative.

PDF page dimensions must be finite within 1..14400 points, with 1..1000 pages,
at most 100000 text runs, and at most 16 MiB of text content. Each run must be
single-line without tabs or Unicode U+2028/U+2029 separators, its X/Y coordinates finite and within the page, its
font size within 1..1000 points, and its font family nonempty and at most 31
UTF-16 code units (matching the shared Windows backend limit).
Pango shapes complex scripts, performs automatic paragraph bidi layout, and
selects fallback fonts from the installed inventory. Absolute font sizes map
directly to PDF points; the first Pango baseline is placed at the requested Y.
Automatic wrapping and tab expansion remain outside this implementation.
The shared display-list format still has no bold/italic/underline fields. Clipping at the page boundary remains possible. The
configured queue controls the physical paper and scaling; PDF canvas dimensions
do not negotiate driver paper settings.

## Runtime requirements and errors

Requires 64-bit glibc Linux (x86-64 or ARM64), CUPS 2's versioned
`libcups.so.2`, and a reachable configured CUPS server for enumeration and
submission. The runtime package is typically `libcups2t64` on Debian 13 or
Ubuntu 24.04, or `libcups2` on older distributions. These helpers do not install
or configure a server or printer. CUPS 3's new API is outside this backend.
`PrintPages` and `ExportPDF` additionally require `libcairo.so.2`,
`libpangocairo-1.0.so.0`, `libpango-1.0.so.0`, and `libgobject-2.0.so.0`,
with suitable installed fonts. `ExportPDF` does not require a CUPS server or
call CUPS. `IsAvailable()` intentionally continues to probe only CUPS; missing
rendering libraries are reported when rendering pages.

The module uses `Optional Declare`, so an application can still start without
the optional CUPS library. Calling a missing symbol raises
`LibraryUnavailableException`. Invalid inputs raise `InvalidArgumentException`;
native failures raise `RuntimeException`. CUPS errors retain the IPP/CUPS status
in `ErrorCode`; temporary-file errors retain `errno`. Unsupported platforms
raise `UnsupportedOperationException`, while the two capability queries remain
safe. Server errors are distinct from a successful empty printer list. CUPS's
`client-error-not-found` response for an empty server is treated as an empty
list rather than as a missing backend.

The native `cups_dest_t` record uses the LP64 CUPS 2 layout: two pointers, two
32-bit integers, then an options pointer (32 bytes, alignment 8). Destination
strings are copied before `cupsFreeDests`, and no native pointers escape.
