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


def slide_xml(paragraphs: str, text_body_prefix: str = "p") -> ElementTree.Element:
    return ElementTree.fromstring(
        f"""<p:sld xmlns:p="{validator.PRESENTATION_NS}"
                    xmlns:a="{validator.DRAWING_NS}">
          <p:cSld><p:spTree><p:sp><{text_body_prefix}:txBody>
            <a:bodyPr/><a:lstStyle/>{paragraphs}
          </{text_body_prefix}:txBody></p:sp></p:spTree></p:cSld>
        </p:sld>"""
    )


class MultilineLineSpacingTests(unittest.TestCase):
    def test_accepts_explicit_break_with_150_percent_spacing(self):
        slide = slide_xml(
            '<a:p><a:pPr><a:lnSpc><a:spcPct val="150000"/>'
            '</a:lnSpc></a:pPr><a:r><a:t>第一行</a:t></a:r><a:br/>'
            '<a:r><a:t>第二行</a:t></a:r></a:p>'
        )
        self.assertEqual(validator.multiline_line_spacing_issues(slide), [])

    def test_rejects_explicit_break_without_spacing(self):
        slide = slide_xml(
            '<a:p><a:r><a:t>第一行</a:t></a:r><a:br/>'
            '<a:r><a:t>第二行</a:t></a:r></a:p>'
        )
        self.assertEqual(
            validator.multiline_line_spacing_issues(slide), [None]
        )

    def test_checks_every_nonempty_paragraph_in_multiline_textbox(self):
        slide = slide_xml(
            '<a:p><a:pPr><a:lnSpc><a:spcPct val="150000"/>'
            '</a:lnSpc></a:pPr><a:r><a:t>第一段</a:t></a:r></a:p>'
            '<a:p><a:pPr><a:lnSpc><a:spcPct val="120000"/>'
            '</a:lnSpc></a:pPr><a:r><a:t>第二段</a:t></a:r></a:p>'
        )
        self.assertEqual(
            validator.multiline_line_spacing_issues(slide), [120_000]
        )

    def test_does_not_require_spacing_for_single_line_text(self):
        slide = slide_xml('<a:p><a:r><a:t>单行标题</a:t></a:r></a:p>')
        self.assertEqual(validator.multiline_line_spacing_issues(slide), [])

    def test_checks_drawing_namespace_text_bodies_such_as_table_cells(self):
        slide = slide_xml(
            '<a:p><a:r><a:t>第一段</a:t></a:r></a:p>'
            '<a:p><a:r><a:t>第二段</a:t></a:r></a:p>',
            text_body_prefix="a",
        )
        self.assertEqual(
            validator.multiline_line_spacing_issues(slide), [None, None]
        )


if __name__ == "__main__":
    unittest.main()
