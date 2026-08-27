#!/usr/bin/env python3
from __future__ import annotations

import argparse
from io import BytesIO
import os
from pathlib import Path
import re
import sys
import tempfile
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
LOCK_ELEMENT_TAGS = {
    f"{{{DRAWING_NS}}}spLocks",
    f"{{{DRAWING_NS}}}picLocks",
    f"{{{DRAWING_NS}}}cxnSpLocks",
    f"{{{DRAWING_NS}}}grpSpLocks",
}
TRUE_VALUES = {"1", "true"}
SLIDE_PART = re.compile(r"^ppt/slides/slide\d+\.xml$")
RESERVED_PREFIX = re.compile(r"^ns\d+$")


def register_namespaces(xml_bytes: bytes) -> None:
    for _, (prefix, uri) in ElementTree.iterparse(
        BytesIO(xml_bytes), events=("start-ns",)
    ):
        if not RESERVED_PREFIX.match(prefix):
            ElementTree.register_namespace(prefix, uri)


def normalize_slide(xml_bytes: bytes) -> tuple[bytes, int]:
    register_namespaces(xml_bytes)
    slide = ElementTree.fromstring(xml_bytes)
    removed = 0

    for element in slide.iter():
        if element.tag not in LOCK_ELEMENT_TAGS:
            continue
        if element.get("noGrp", "").lower() not in TRUE_VALUES:
            continue
        del element.attrib["noGrp"]
        removed += 1

    if not removed:
        return xml_bytes, 0

    return (
        ElementTree.tostring(slide, encoding="utf-8", xml_declaration=True),
        removed,
    )


def normalize_pptx(source: Path, output: Path) -> tuple[int, int]:
    output.parent.mkdir(parents=True, exist_ok=True)
    same_target = source.resolve() == output.resolve()
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    os.close(descriptor)
    temp_path = Path(temp_name)
    removed = 0
    changed_slides = 0

    try:
        with ZipFile(source) as source_archive, ZipFile(temp_path, "w") as output_archive:
            output_archive.comment = source_archive.comment
            for entry in source_archive.infolist():
                data = source_archive.read(entry)
                if SLIDE_PART.match(entry.filename):
                    data, entry_removed = normalize_slide(data)
                    if entry_removed:
                        removed += entry_removed
                        changed_slides += 1
                output_archive.writestr(entry, data)

        if same_target and not removed:
            temp_path.unlink()
        else:
            os.replace(temp_path, output)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    return removed, changed_slides


def fail(message: str) -> int:
    print(f"FAIL {message}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Remove active noGrp locks from slide objects while preserving all other "
            "PowerPoint locks and package parts."
        )
    )
    parser.add_argument("pptx", type=Path, help="Input PowerPoint .pptx file")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path; omit to update the input file atomically",
    )
    args = parser.parse_args()

    source = args.pptx.resolve()
    output = args.output.resolve() if args.output else source
    if source.suffix.lower() != ".pptx":
        return fail(f"expected a .pptx file: {source}")
    if output.suffix.lower() != ".pptx":
        return fail(f"output must use the .pptx extension: {output}")
    if not source.is_file():
        return fail(f"file does not exist: {source}")

    try:
        removed, changed_slides = normalize_pptx(source, output)
    except BadZipFile:
        return fail(f"file is not a valid ZIP-based PPTX package: {source}")
    except (OSError, ElementTree.ParseError, ValueError) as exc:
        return fail(f"could not normalize PPTX: {exc}")

    if removed:
        print(
            f"PASS removed {removed} active noGrp locks from "
            f"{changed_slides} slide XML part(s): {output}"
        )
    else:
        print(f"PASS no active noGrp locks found: {output}")
    print("INFO Preserved noMove, noResize, noTextEdit, and all other lock attributes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
