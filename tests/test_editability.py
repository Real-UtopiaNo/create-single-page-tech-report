from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from xml.etree import ElementTree


SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = SKILL_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


normalizer = load_script("normalize_groupability.py")
validator = load_script("validate_single_page_report.py")


SLIDE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree><p:sp>
    <p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr>
      <a:spLocks noGrp="1" noMove="true" noResize="1" noSelect="1"
                 noTextEdit="true" noRot="1"/>
    </p:cNvSpPr><p:nvPr/></p:nvSpPr>
    <p:txBody><a:bodyPr/><a:lstStyle/><a:p>
      <a:pPr><a:defRPr><a:solidFill><a:srgbClr val="C7000B"/></a:solidFill></a:defRPr></a:pPr>
      <a:r><a:rPr><a:solidFill><a:srgbClr val="C7000B"/></a:solidFill><a:latin typeface="Arial"/></a:rPr><a:t>Petals </a:t></a:r>
      <a:r><a:rPr><a:solidFill><a:srgbClr val="C7000B"/></a:solidFill><a:ea typeface="Microsoft YaHei"/></a:rPr><a:t>恢复</a:t></a:r>
    </a:p></p:txBody>
  </p:sp></p:spTree></p:cSld>
</p:sld>""".encode("utf-8")


MIXED_COLOR_XML = SLIDE_XML.replace(
    b'<a:srgbClr val="C7000B"/></a:solidFill><a:ea',
    b'<a:srgbClr val="115CAA"/></a:solidFill><a:ea',
)


class EditabilityNormalizationTests(unittest.TestCase):
    def test_removes_edit_locks_and_redundant_run_colors(self):
        normalized, removed_locks, removed_colors = normalizer.normalize_slide(
            SLIDE_XML
        )
        self.assertEqual(removed_locks, 5)
        self.assertEqual(removed_colors, 2)
        root = ElementTree.fromstring(normalized)
        locks = next(
            element
            for element in root.iter()
            if element.tag.endswith("spLocks")
        )
        self.assertEqual(locks.get("noRot"), "1")
        for attribute in normalizer.EDIT_BLOCKING_LOCKS:
            self.assertNotIn(attribute, locks.attrib)
        self.assertEqual(validator.redundant_run_color_count(root), 0)

    def test_preserves_intentional_mixed_run_colors(self):
        normalized, _, removed_colors = normalizer.normalize_slide(MIXED_COLOR_XML)
        self.assertEqual(removed_colors, 1)
        root = ElementTree.fromstring(normalized)
        colors = [
            element.get("val")
            for element in root.iter()
            if element.tag.endswith("srgbClr")
        ]
        self.assertIn("C7000B", colors)
        self.assertIn("115CAA", colors)


if __name__ == "__main__":
    unittest.main()
