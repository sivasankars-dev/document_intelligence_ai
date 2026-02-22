import sys
from pathlib import Path
from types import SimpleNamespace

from services.ingestion_service.parser_service import extract_text_from_document


def test_extract_text_file(tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello world", encoding="utf-8")

    text = extract_text_from_document(str(file_path))

    assert "hello world" in text


def test_extract_eml(tmp_path):
    file_path = tmp_path / "mail.eml"
    file_path.write_text(
        "Subject: Renewal Notice\nFrom: a@example.com\nTo: b@example.com\n\nPolicy renewal due next month.",
        encoding="utf-8",
    )

    text = extract_text_from_document(str(file_path))

    assert "Subject: Renewal Notice" in text
    assert "Policy renewal due next month." in text


def test_extract_docx_with_monkeypatched_module(monkeypatch, tmp_path):
    file_path = tmp_path / "contract.docx"
    file_path.write_text("placeholder", encoding="utf-8")

    fake_doc = SimpleNamespace(paragraphs=[SimpleNamespace(text="Clause 1"), SimpleNamespace(text="Clause 2")])
    monkeypatch.setitem(
        sys.modules,
        "docx",
        SimpleNamespace(Document=lambda _path: fake_doc),
    )

    text = extract_text_from_document(str(file_path))

    assert "Clause 1" in text
    assert "Clause 2" in text


def test_extract_html_with_monkeypatched_bs4(monkeypatch, tmp_path):
    file_path = tmp_path / "policy.html"
    file_path.write_text("<html><body><h1>Policy</h1><p>Coverage details</p></body></html>", encoding="utf-8")

    class _FakeSoup:
        def __init__(self, html, parser):
            self.html = html
            self.parser = parser

        def get_text(self, separator="\n", strip=True):
            return "Policy\nCoverage details"

    monkeypatch.setitem(sys.modules, "bs4", SimpleNamespace(BeautifulSoup=_FakeSoup))

    text = extract_text_from_document(str(file_path))
    assert "Coverage details" in text


def test_extract_unsupported_type(tmp_path):
    file_path = tmp_path / "archive.zip"
    file_path.write_text("data", encoding="utf-8")

    try:
        extract_text_from_document(str(file_path))
        assert False, "Expected ValueError for unsupported type"
    except ValueError as exc:
        assert "Unsupported document type" in str(exc)
