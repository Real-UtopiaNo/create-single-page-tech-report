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
EDIT_BLOCKING_LOCKS = {"noGrp", "noMove", "noResize", "noSelect", "noTextEdit"}
TRUE_VALUES = {"1", "true"}
SLIDE_PART = re.compile(r"^ppt/slides/slide\d+\.xml$")
RESERVED_PREFIX = re.compile(r"^ns\d+$")


def register_namespaces(xml_bytes: bytes) -> None:
    for _, (prefix, uri) in ElementTree.iterparse(
        BytesIO(xml_bytes), events=("start-ns",)
    ):
        if not RESERVED_PREFIX.match(prefix):
            ElementTree.register_namespace(prefix, uri)


def _solid_rgb(parent: ElementTree.Element | None) -> str | None:
    if parent is None:
        return None
    color = parent.find(
        f"{{{DRAWING_NS}}}solidFill/{{{DRAWING_NS}}}srgbClr"
    )
    return color.get("val", "").upper() if color is not None else None


def _remove_redundant_run_colors(slide: ElementTree.Element) -> int:
    removed = 0
    paragraph_tag = f"{{{DRAWING_NS}}}p"
    run_tag = f"{{{DRAWING_NS}}}r"
    run_props_tag = f"{{{DRAWING_NS}}}rPr"
    default_props_path = (
        f"{{{DRAWING_NS}}}pPr/{{{DRAWING_NS}}}defRPr"
    )
    text_tag = f"{{{DRAWING_NS}}}t"
    solid_fill_tag = f"{{{DRAWING_NS}}}solidFill"

    for paragraph in slide.iter(paragraph_tag):
        default_color = _solid_rgb(paragraph.find(default_props_path))
        if not default_color:
            continue
        runs = [
            run
            for run in paragraph.findall(run_tag)
            if run.findtext(text_tag) is not None
        ]
        if not runs:
            continue
        for run in runs:
            props = run.find(run_props_tag)
            if _solid_rgb(props) != default_color:
                continue
            solid_fill = props.find(solid_fill_tag) if props is not None else None
            if solid_fill is not None:
                props.remove(solid_fill)
                removed += 1
    return removed


def normalize_slide(xml_bytes: bytes) -> tuple[bytes, int, int]:
    register_namespaces(xml_bytes)
    slide = ElementTree.fromstring(xml_bytes)
    removed_locks = 0

    for element in slide.iter():
        if element.tag not in LOCK_ELEMENT_TAGS:
            continue
        for attribute in EDIT_BLOCKING_LOCKS:
            if element.get(attribute, "").lower() in TRUE_VALUES:
                del element.attrib[attribute]
                removed_locks += 1

    removed_colors = _remove_redundant_run_colors(slide)
    if not removed_locks and not removed_colors:
        return xml_bytes, 0, 0

    return (
        ElementTree.tostring(slide, encoding="utf-8", xml_declaration=True),
        removed_locks,
        removed_colors,
    )


def normalize_pptx(source: Path, output: Path) -> tuple[int, int, int]:
    output.parent.mkdir(parents=True, exist_ok=True)
    same_target = source.resolve() == output.resolve()
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    os.close(descriptor)
    temp_path = Path(temp_name)
    removed_locks = 0
    removed_colors = 0
    changed_slides = 0

    try:
        with ZipFile(source) as source_archive, ZipFile(temp_path, "w") as output_archive:
            output_archive.comment = source_archive.comment
            for entry in source_archive.infolist():
                data = source_archive.read(entry)
                if SLIDE_PART.match(entry.filename):
                    data, entry_locks, entry_colors = normalize_slide(data)
                    if entry_locks or entry_colors:
                        removed_locks += entry_locks
                        removed_colors += entry_colors
                        changed_slides += 1
                output_archive.writestr(entry, data)

        if same_target and not removed_locks and not removed_colors:
            temp_path.unlink()
        else:
            os.replace(temp_path, output)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    return removed_locks, removed_colors, changed_slides


def fail(message: str) -> int:
    print(f"FAIL {message}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Remove locks that block routine editing and redundant run-level colors "
            "that override a matching paragraph default."
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
        removed_locks, removed_colors, changed_slides = normalize_pptx(source, output)
    except BadZipFile:
        return fail(f"file is not a valid ZIP-based PPTX package: {source}")
    except (OSError, ElementTree.ParseError, ValueError) as exc:
        return fail(f"could not normalize PPTX: {exc}")

    print(
        "PASS normalized convenient editability: "
        f"removed {removed_locks} edit-blocking lock attribute(s) and "
        f"{removed_colors} redundant run-level color override(s) from "
        f"{changed_slides} slide XML part(s): {output}"
    )
    print(
        "INFO Preserved mixed-color emphasis and locks unrelated to routine "
        "selection, movement, resizing, grouping, and text editing."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
