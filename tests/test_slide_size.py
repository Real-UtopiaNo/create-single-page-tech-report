from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from xml.etree import ElementTree


SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = SKILL_ROOT / "scripts" / "validate_single_page_report.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def presentation_xml(width: int | None, height: int | None) -> ElementTree.Element:
    size = "" if width is None else f'<p:sldSz cx="{width}" cy="{height}"/>'
    return ElementTree.fromstring(
        f'<p:presentation xmlns:p="{validator.PRESENTATION_NS}">{size}</p:presentation>'
    )


class StandardWidescreenSizeTests(unittest.TestCase):
    def test_accepts_powerpoint_standard_widescreen_physical_size(self):
        presentation = presentation_xml(
            validator.STANDARD_WIDESCREEN_CX,
            validator.STANDARD_WIDESCREEN_CY,
        )
        self.assertIsNone(validator.standard_widescreen_size_issue(presentation))

    def test_rejects_same_aspect_ratio_with_larger_physical_canvas(self):
        presentation = presentation_xml(15_240_000, 8_572_500)
        issue = validator.standard_widescreen_size_issue(presentation)
        self.assertIsNotNone(issue)
        self.assertIn("16:9 aspect ratio alone is insufficient", issue)

    def test_rejects_missing_slide_size(self):
        presentation = presentation_xml(None, None)
        self.assertEqual(
            validator.standard_widescreen_size_issue(presentation),
            "presentation.xml is missing p:sldSz",
        )


if __name__ == "__main__":
    unittest.main()
