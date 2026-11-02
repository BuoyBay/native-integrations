# Native printing for Linux and Windows

`printing.bui` is a shared Buoy API over native CUPS/Pango/Cairo and Windows GDI/WinSpool backends. Keep `integrations/printing/` and the relevant platform directory in their relative locations when copying these modules into another project. No additional Buoy packages are required. The macOS backend is not included here.

The interface follows the [Xojo PrinterSetup model](https://docs.xojo.com/api/printing/printersetup.html) and [Graphics drawing conventions](https://docs.xojo.com/api/graphics/graphics.html): open a drawing surface, set its font, draw text at a baseline, and advance with `NextPage`. The older global `OpenPrinter` spelling is also available. This is a text-printing subset with its own `PrinterGraphics` class; it does not extend Buoy's built-in `Graphics`.

## Drawing interface

| API | Behavior |
| --- | --- |
| `PrinterSetup.PrinterName` | Explicit queue name; empty selects the OS default when opening |
| `PrinterSetup.JobName` | Document title, default `Buoy document` |
| `PrinterSetup.PageWidth`, `PageHeight` | Logical page canvas in points; defaults to A4 |
| `PrinterSetup.Landscape` | Swaps portrait logical dimensions when opening |
| `HorizontalResolution`, `VerticalResolution` | Logical resolution, 72 points per inch |
| `PrinterSetup.OpenPrinter(setup)` / `OpenPrinter(setup)` | Snapshots setup and returns buffered `PrinterGraphics`; no job is submitted |
| `PrinterSetup.OpenPrinter()` / `OpenPrinter()` | Uses a default setup |
| `PrinterGraphics.FontName`, `FontSize` | Font family and point size, default `System` and 12 |
| `DrawText(str, x, y)` | Single-line text at x and baseline y, in points |
| `NextPage()` | Adds a new page, including an intentionally blank page |
| `Width`, `Height`, `PageCount` | Logical canvas dimensions and buffered page count |
| `Close()` | Submits once and returns a positive native spool job ID |
| `Cancel()` | Discards buffered pages before submission |
| `IsClosed`, `PrintingCancelled`, `JobId` | Drawing/submission state |

See [example.bui](example.bui) for a complete program. It submits only when explicitly run with `--print`. Set `PrinterName` before opening to select a queue instead of the default. Drawing with an explicit name does not probe whether that queue exists; the backend validates it at submission.

Call `Close` to print. Dropping the drawing object never submits a job. This explicit lifecycle differs from Xojo's automatic completion when graphics goes out of scope. A submission attempt is terminal even if it fails, preventing an automatic retry from creating duplicate output. After submission, `Cancel` does not cancel the spooler's job. Repeated `Close` returns the recorded job ID, or zero after cancellation/failed submission.

## Scope and native behavior

Logical coordinates are independent of printer DPI. Linux renders pages to a Cairo PDF and submits that PDF to CUPS; Windows converts points to device coordinates and draws through GDI. `PageWidth`/`PageHeight` describe the drawing canvas, not negotiated printer media. Windows retains the driver's paper settings and clips to the logical/printable area without scaling; CUPS media/filter behavior follows the queue configuration. Choose compatible paper settings in the native printer configuration. No paper-size selection, printer/page-setup dialogs, saved `Settings`, copies, page ranges, color graphics, pictures, lines, or shapes are implemented yet.

`DrawText` supports a single line without CR/LF/tab, with no wrapping/condensing parameters. Coordinates must lie within the logical page, font sizes within 1..1000 points, and font names within 31 UTF-16 code units. `System`/`SmallSystem` select the native default family. Linux uses Pango for complex-script shaping, bidirectional layout and installed-font fallback. Windows uses GDI; identical text layout across operating systems is not guaranteed.

Documents are bounded to 1000 pages, 100000 text runs, and 16 MiB of UTF-8 text; page dimensions are 1..14400 points. Setup and drawing objects are intended for use on one thread. Native errors are exceptions, rather than the Nil/cancellation conventions used by some Xojo printing methods.

## Discovery and convenience calls

The module also exports `IsSupported`, `IsAvailable`, `Printers`, `DefaultPrinter`, and `PrintText(printerName, title, text)`. `Printers` returns owned `PrinterInfo` objects with `Name` and `IsDefault`; `DefaultPrinter` returns `Optional Of String`. `IsAvailable` reports library capability, not a running spooler or a configured printer. `PrintText` immediately submits text to an explicitly selected printer, using the backend's text-layout policy.

Backend requirements, detailed errors and runtime evidence:

- [Linux CUPS and Cairo](../linux/printing-README.md)
- [Windows GDI and WinSpool](../windows/printing-README.md)

## Canonical package migration

New consumers can use `Import printing` from the sealed `libraries/printing` package. Its buffered setup is named `PrintJobSetup`; retain this source facade for callers using writable Double `PrinterSetup.PageWidth/PageHeight`. The package's existing macOS `PrinterSetup` has read-only Integer geometry and is not a replacement for this type. This facade and its native backends remain unchanged and independently usable.

Do not import both surfaces in one consumer, even with module aliases: the compiler rejects duplicate class declarations. The consolidation test records that rejection on all six targets. A safe mixed-import adapter remains unproven. Migrate imports and buffered setup names together; the canonical package additionally exposes feature capabilities and terminal submission state/failure. Neither surface implements buffered dialogs, negotiated paper selection, copies or page ranges.
