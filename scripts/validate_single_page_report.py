#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
GROUPING_LOCK_TAGS = {
    f"{{{DRAWING_NS}}}spLocks",
    f"{{{DRAWING_NS}}}picLocks",
    f"{{{DRAWING_NS}}}cxnSpLocks",
    f"{{{DRAWING_NS}}}grpSpLocks",
}
TRUE_VALUES = {"1", "true"}


def fail(message: str) -> int:
    print(f"FAIL {message}")
    return 1


def parse_xml(archive: ZipFile, member: str) -> ElementTree.Element:
    try:
        return ElementTree.fromstring(archive.read(member))
    except KeyError as exc:
        raise ValueError(f"missing required PPTX part: {member}") from exc
    except ElementTree.ParseError as exc:
        raise ValueError(f"invalid XML in {member}: {exc}") from exc


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            for required in ("[Content_Types].xml", "ppt/presentation.xml"):
                if required not in names:
                    errors.append(f"missing required PPTX part: {required}")

            if errors:
                return errors

            presentation = parse_xml(archive, "ppt/presentation.xml")
            slide_ids = presentation.findall(f".//{{{PRESENTATION_NS}}}sldId")
            slide_parts = sorted(
                name
                for name in names
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )

            if len(slide_ids) != 1:
                errors.append(
                    f"presentation.xml declares {len(slide_ids)} slides; exactly 1 is required"
                )
            if len(slide_parts) != 1:
                errors.append(
                    f"archive contains {len(slide_parts)} slide XML parts; exactly 1 is required"
                )

            for slide_part in slide_parts:
                slide = parse_xml(archive, slide_part)
                timing_nodes = slide.findall(f".//{{{PRESENTATION_NS}}}timing")
                if timing_nodes:
                    errors.append(
                        f"{slide_part} contains PowerPoint timing/animation nodes"
                    )
                grouping_locks = [
                    element
                    for element in slide.iter()
                    if element.tag in GROUPING_LOCK_TAGS
                    and element.get("noGrp", "").lower() in TRUE_VALUES
                ]
                if grouping_locks:
                    errors.append(
                        f"{slide_part} contains {len(grouping_locks)} active noGrp "
                        "lock(s) that disable PowerPoint grouping; run "
                        "scripts/normalize_groupability.py before validation"
                    )
    except BadZipFile:
        errors.append("file is not a valid ZIP-based PPTX package")
    except OSError as exc:
        errors.append(f"cannot read file: {exc}")
    except ValueError as exc:
        errors.append(str(exc))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the machine-checkable contract of a single-page technical report."
    )
    parser.add_argument("pptx", type=Path, help="Path to the PowerPoint .pptx file")
    args = parser.parse_args()

    path = args.pptx.resolve()
    if path.suffix.lower() != ".pptx":
        return fail(f"expected a .pptx file: {path}")
    if not path.is_file():
        return fail(f"file does not exist: {path}")

    errors = validate(path)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1

    print(
        "PASS valid single-slide PPTX without animation timing nodes or active "
        f"noGrp locks: {path}"
    )
    print(
        "INFO Manually review title semantics, evidence boundaries, fonts, body font size, "
        "colors, overflow, overlap, chart clarity, and the bottom insight."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
