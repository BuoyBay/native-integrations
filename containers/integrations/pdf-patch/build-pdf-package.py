#!/usr/bin/env python3
"""Build a locally patched Buoy pdf package from the stock pdf-2.4.6.buipkg.

The stock archive is never modified. The script verifies its pinned SHA-256,
extracts it to a temporary directory, applies PDF.bui.patch, adds four
existing libharu functions to the export tables of both Windows pdf.dll
files, regenerates their import libraries with llvm-dlltool, and re-seals the
tree with `buoy pkg seal`, which writes a new manifest with per-file xxh64
hashes and package digest.

Usage:
    python3 -I build-pdf-package.py STOCK.buipkg OUTPUT.buipkg
        [--buoy /usr/bin/buoy] [--dlltool llvm-dlltool]

Only the Python standard library is used. `buoy` (0.72.0) and
`llvm-dlltool` (LLVM 15 or later) must be installed.
"""

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PATCH = os.path.join(HERE, "PDF.bui.patch")

STOCK_SHA256 = "0146c952bcfa8f7d8ba71a78c57c88538a76eb27d2dd40e94f1ca12a6a00cccb"
STOCK_FILES = {
    "modules/PDF.bui": "861b2961a8626a9f6c14c3d2b9f53179de6eb1b5a2b5dbe7ea0f75be7de7ef59",
    "runtime/x86_64-pc-windows-msvc/pdf.dll": "8de49ec0b05ea217bab5aa14d00723092305f80fbad8431ae37093955fe64f95",
    "runtime/aarch64-pc-windows-msvc/pdf.dll": "44b8162f70e8479ce387e6fccaa61faadf070b8ad94942111b6c7cabdc3309cd",
    "link/x86_64-pc-windows-msvc/pdf.lib": "8daee2ea98a38eb53f16731739d6f3751ba83f422357ba3a4e74d3c9971c742b",
    "link/aarch64-pc-windows-msvc/pdf.lib": "c43362764c0c4550e4bf0cf2ce0e80512c6368bd314712b8b31cd9f3a5199fa2",
}
# libharu functions compiled into both Windows DLLs but not exported by them.
# Linux and macOS libraries already export all four.
NEW_EXPORTS = [
    "HPDF_CreateExtGState",
    "HPDF_ExtGState_SetAlphaFill",
    "HPDF_ExtGState_SetAlphaStroke",
    "HPDF_Page_SetExtGState",
]
WINDOWS = {
    "x86_64-pc-windows-msvc": (0x8664, "i386:x86-64"),
    "aarch64-pc-windows-msvc": (0xAA64, "arm64"),
}
DESCRIPTION_SUFFIX = (
    " [local Object2D patch: recorded IGraphics paths, ExtGState alpha;"
    " built by integrations/pdf-patch from stock pdf-2.4.6]"
)
# Fixed archive timestamp, so identical inputs seal to identical bytes.
EPOCH = 1735689600  # 2025-01-01T00:00:00Z


def fail(message):
    sys.exit("build-pdf-package: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def extract(archive, destination):
    with zipfile.ZipFile(archive) as package:
        for info in package.infolist():
            name = info.filename
            parts = name.split("/")
            if name.startswith("/") or "\\" in name or ".." in parts or not name:
                fail("unsafe archive path: " + name)
            target = os.path.join(destination, *parts)
            if name.endswith("/"):
                os.makedirs(target, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with package.open(info) as source, open(target, "wb") as output:
                shutil.copyfileobj(source, output)
            mode = (info.external_attr >> 16) & 0o777
            os.chmod(target, 0o755 if mode & 0o111 else 0o644)


# ── Unified diff application (exact context, no fuzz) ──────────────────────
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def apply_patch(original, patch_text):
    source = original.split("\n")
    lines = patch_text.split("\n")
    output = []
    cursor = 0
    index = 0
    while index < len(lines) and not lines[index].startswith("@@"):
        index += 1
    while index < len(lines):
        match = HUNK.match(lines[index])
        if not match:
            if lines[index] == "":
                index += 1
                continue
            fail("malformed patch line: " + lines[index][:60])
        start = int(match.group(1)) - 1
        if match.group(2) == "0":
            start += 1
        if start < cursor:
            fail("overlapping hunks in patch")
        output.extend(source[cursor:start])
        cursor = start
        index += 1
        while index < len(lines) and not lines[index].startswith("@@"):
            line = lines[index]
            index += 1
            if line.startswith("\\"):
                continue
            if line == "" and index == len(lines):
                break
            tag, text = line[:1], line[1:]
            if tag in (" ", "-"):
                if cursor >= len(source) or source[cursor] != text:
                    fail("patch context does not match source at line %d" % (cursor + 1))
                cursor += 1
                if tag == " ":
                    output.append(text)
            elif tag == "+":
                output.append(text)
            else:
                fail("malformed patch line: " + line[:60])
    output.extend(source[cursor:])
    return "\n".join(output)


# ── PE export-table extension ──────────────────────────────────────────────
def align(value, boundary):
    return (value + boundary - 1) // boundary * boundary


def c_string(data, offset):
    end = data.index(b"\0", offset)
    return data[offset:end].decode("ascii")


def add_exports(path, machine, names):
    data = bytearray(open(path, "rb").read())
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        fail(path + ": not a PE image")
    coff = pe + 4
    (file_machine, section_count, _, symbol_offset, symbol_count,
     optional_size, _) = struct.unpack_from("<HHIIIHH", data, coff)
    if file_machine != machine:
        fail("%s: machine 0x%x, expected 0x%x" % (path, file_machine, machine))
    optional = coff + 20
    if struct.unpack_from("<H", data, optional)[0] != 0x20B:
        fail(path + ": not PE32+")
    section_alignment, file_alignment = struct.unpack_from("<II", data, optional + 32)
    size_of_headers = struct.unpack_from("<I", data, optional + 60)[0]
    directories = optional + 112
    if struct.unpack_from("<II", data, directories + 4 * 8) != (0, 0):
        fail(path + ": signed images are not supported")
    table = optional + optional_size

    sections = []
    for i in range(section_count):
        raw = struct.unpack_from("<8sIIII", data, table + 40 * i)
        sections.append({"name": raw[0], "vsize": raw[1], "va": raw[2],
                         "rawsize": raw[3], "rawptr": raw[4]})

    def offset_of(rva):
        for section in sections:
            if section["va"] <= rva < section["va"] + max(section["vsize"], section["rawsize"]):
                return rva - section["va"] + section["rawptr"]
        fail("%s: RVA 0x%x is outside every section" % (path, rva))

    # Existing exports, kept with their original ordinals.
    export_rva = struct.unpack_from("<I", data, directories)[0]
    base = offset_of(export_rva)
    (_, _, _, _, dll_name_rva, ordinal_base, function_count, name_count,
     functions_rva, names_rva, ordinals_rva) = struct.unpack_from("<IIHHIIIIIII", data, base)
    dll_name = c_string(data, offset_of(dll_name_rva))
    functions = [struct.unpack_from("<I", data, offset_of(functions_rva) + 4 * i)[0]
                 for i in range(function_count)]
    exported = {}
    for i in range(name_count):
        name = c_string(data, offset_of(struct.unpack_from("<I", data, offset_of(names_rva) + 4 * i)[0]))
        exported[name] = struct.unpack_from("<H", data, offset_of(ordinals_rva) + 2 * i)[0]
    for name in names:
        if name in exported:
            fail("%s: %s is already exported" % (path, name))

    # Locate the new functions in the COFF symbol table: external, function
    # type, defined in an executable section.
    strings = symbol_offset + 18 * symbol_count
    found = {}
    i = 0
    while i < symbol_count:
        record = symbol_offset + 18 * i
        raw_name, value, section_number, symbol_type, storage, aux = struct.unpack_from(
            "<8sIhHBB", data, record)
        if raw_name[:4] == b"\0\0\0\0":
            name = c_string(data, strings + struct.unpack_from("<I", raw_name, 4)[0])
        else:
            name = raw_name.rstrip(b"\0").decode("ascii", "replace")
        if name in names and storage == 2 and symbol_type == 0x20 and section_number > 0:
            section = sections[section_number - 1]
            characteristics = struct.unpack_from("<I", data, table + 40 * (section_number - 1) + 36)[0]
            if not characteristics & 0x20000000:
                fail("%s: %s is not in an executable section" % (path, name))
            if name in found:
                fail("%s: duplicate symbol %s" % (path, name))
            found[name] = section["va"] + value
        i += 1 + aux
    missing = [name for name in names if name not in found]
    if missing:
        fail("%s: symbols not found: %s" % (path, ", ".join(missing)))

    entries = [(name, ordinal_base + ordinal) for name, ordinal in exported.items()]
    for name in names:
        functions.append(found[name])
        entries.append((name, ordinal_base + len(functions) - 1))
    entries.sort(key=lambda entry: entry[0].encode("ascii"))

    # New .edata section after the last mapped section; raw data at the end
    # of the file, after the COFF symbol and string tables.
    header_end = table + 40 * (section_count + 1)
    if header_end > size_of_headers or header_end > min(s["rawptr"] for s in sections if s["rawptr"]):
        fail(path + ": no room for another section header")
    va = align(max(s["va"] + s["vsize"] for s in sections), section_alignment)
    count = len(functions)
    directory_size = 40
    eat = directory_size
    name_pointers = eat + 4 * count
    ordinal_table = name_pointers + 4 * len(entries)
    strings_at = ordinal_table + 2 * len(entries)
    blob = bytearray(strings_at)
    dll_name_at = len(blob)
    blob += dll_name.encode("ascii") + b"\0"
    name_rvas = []
    for name, _ in entries:
        name_rvas.append(va + len(blob))
        blob += name.encode("ascii") + b"\0"
    struct.pack_into("<IIHHIIIIIII", blob, 0, 0, 0, 0, 0, va + dll_name_at, ordinal_base,
                     count, len(entries), va + eat, va + name_pointers, va + ordinal_table)
    for i, rva in enumerate(functions):
        struct.pack_into("<I", blob, eat + 4 * i, rva)
    for i, (_, ordinal) in enumerate(entries):
        struct.pack_into("<I", blob, name_pointers + 4 * i, name_rvas[i])
        struct.pack_into("<H", blob, ordinal_table + 2 * i, ordinal - ordinal_base)
    virtual_size = len(blob)
    raw_size = align(virtual_size, file_alignment)
    raw_pointer = align(len(data), file_alignment)
    data += b"\0" * (raw_pointer - len(data))
    data += blob + b"\0" * (raw_size - virtual_size)

    struct.pack_into("<8sIIIIIIHHI", data, table + 40 * section_count, b".edata\0\0",
                     virtual_size, va, raw_size, raw_pointer, 0, 0, 0, 0, 0x40000040)
    struct.pack_into("<H", data, coff + 2, section_count + 1)
    initialized = struct.unpack_from("<I", data, optional + 8)[0]
    struct.pack_into("<I", data, optional + 8, initialized + raw_size)
    struct.pack_into("<I", data, optional + 56, align(va + virtual_size, section_alignment))
    struct.pack_into("<II", data, directories, va, virtual_size)
    open(path, "wb").write(bytes(data))
    return dll_name, [name for name, _ in entries], found


def find_dlltool(explicit):
    candidates = [explicit] if explicit else ["llvm-dlltool"] + sorted(
        glob.glob("/usr/lib/llvm-*/bin/llvm-dlltool"), reverse=True)
    for candidate in candidates:
        resolved = shutil.which(candidate) if candidate else None
        if resolved:
            return resolved
    fail("llvm-dlltool not found; install LLVM or pass --dlltool")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("stock", help="stock pdf-2.4.6.buipkg (left unmodified)")
    parser.add_argument("output", help="patched .buipkg to write")
    # /usr/bin/buoy is preferred on Linux: this workspace's /usr/local/bin/buoy
    # wrapper injects compile-only flags that `buoy pkg` rejects.
    default_buoy = "/usr/bin/buoy" if os.path.exists("/usr/bin/buoy") else (shutil.which("buoy") or "buoy")
    parser.add_argument("--buoy", default=default_buoy,
                        help="Buoy 0.72.0 compiler used for `pkg seal`")
    parser.add_argument("--dlltool", help="llvm-dlltool executable")
    args = parser.parse_args()

    if sha256(args.stock) != STOCK_SHA256:
        fail("%s is not the pinned stock pdf-2.4.6.buipkg (sha256 %s)" % (args.stock, STOCK_SHA256))
    dlltool = find_dlltool(args.dlltool)
    output = os.path.abspath(args.output)
    if os.path.realpath(output) == os.path.realpath(args.stock):
        fail("refusing to overwrite the stock package")

    with tempfile.TemporaryDirectory() as work:
        tree = os.path.join(work, "pdf")
        extract(args.stock, tree)
        for relative, expected in STOCK_FILES.items():
            if sha256(os.path.join(tree, relative)) != expected:
                fail("unexpected stock content: " + relative)

        module = os.path.join(tree, "modules", "PDF.bui")
        with open(module, encoding="utf-8", newline="") as stream:
            original = stream.read()
        with open(PATCH, encoding="utf-8", newline="") as stream:
            patched = apply_patch(original, stream.read())
        with open(module, "w", encoding="utf-8", newline="") as stream:
            stream.write(patched)

        for triple, (machine, dlltool_machine) in WINDOWS.items():
            dll = os.path.join(tree, "runtime", triple, "pdf.dll")
            dll_name, exports, found = add_exports(dll, machine, NEW_EXPORTS)
            definition = os.path.join(work, triple + ".def")
            with open(definition, "w", newline="\n") as stream:
                stream.write("LIBRARY %s\nEXPORTS\n" % dll_name)
                for name in exports:
                    stream.write("    %s\n" % name)
            library = os.path.join(tree, "link", triple, "pdf.lib")
            subprocess.run([dlltool, "-m", dlltool_machine, "-d", definition,
                            "-D", dll_name, "-l", library], check=True)
            for name in NEW_EXPORTS:
                print("%s: export %s -> RVA 0x%x" % (triple, name, found[name]))

        with open(os.path.join(tree, "manifest.json"), encoding="utf-8") as stream:
            manifest = json.load(stream)
        for field in ("files", "digest", "platforms", "modules"):
            manifest.pop(field, None)
        manifest["description"] += DESCRIPTION_SUFFIX
        with open(os.path.join(tree, "manifest.json"), "w", encoding="utf-8", newline="\n") as stream:
            json.dump(manifest, stream, indent=2, ensure_ascii=False)
            stream.write("\n")

        for root, directories, files in os.walk(tree):
            for name in directories + files:
                os.utime(os.path.join(root, name), (EPOCH, EPOCH))
        sealed = os.path.join(work, "sealed.buipkg")
        subprocess.run([args.buoy, "pkg", "seal", tree, "-o", sealed],
                       check=True, env={**os.environ, "TZ": "UTC"})
        with zipfile.ZipFile(sealed) as package:
            result = json.loads(package.read("manifest.json"))
            names = set(package.namelist())
        expected = {entry["path"] for entry in result["files"]}
        if not result.get("digest", "").startswith("xxh64:") or expected != names - {"manifest.json"}:
            fail("sealed manifest does not describe the archive")
        if result["modules"] != ["modules/PDF.bui"] or len(result["platforms"]) != 6:
            fail("sealed manifest lost a module or platform")
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        shutil.copyfile(sealed, output)

    print("digest %s" % result["digest"])
    print("sha256 %s  %s" % (sha256(output), output))


if __name__ == "__main__":
    main()
