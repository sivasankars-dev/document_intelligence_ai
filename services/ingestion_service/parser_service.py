from email import policy
from email.parser import BytesParser
from pathlib import Path


def _extract_pdf(path: str) -> str:
    import fitz

    text_content = ""
    with fitz.open(path) as doc:
        for page in doc:
            text_content += page.get_text()
    return text_content


def _extract_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as file:
        return file.read()


def _extract_docx(path: str) -> str:
    try:
        from docx import Document
    except ModuleNotFoundError as exc:
        raise RuntimeError("python-docx package is required for DOCX parsing") from exc

    doc = Document(path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text)


def _extract_csv(path: str) -> str:
    import pandas as pd

    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows = df.fillna("").astype(str).values.tolist()
    lines = []
    if list(df.columns):
        lines.append(", ".join(str(col) for col in df.columns))
    lines.extend(", ".join(row) for row in rows)
    return "\n".join(lines)


def _extract_excel(path: str) -> str:
    import pandas as pd

    sheets = pd.read_excel(path, sheet_name=None, dtype=str)
    blocks = []
    for sheet_name, frame in sheets.items():
        frame = frame.fillna("").astype(str)
        rows = frame.values.tolist()
        lines = [f"Sheet: {sheet_name}"]
        if list(frame.columns):
            lines.append(", ".join(str(col) for col in frame.columns))
        lines.extend(", ".join(row) for row in rows)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _extract_image_ocr(path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise RuntimeError("pytesseract and pillow packages are required for image OCR") from exc

    with Image.open(path) as image:
        return pytesseract.image_to_string(image)


def _extract_eml(path: str) -> str:
    with open(path, "rb") as file:
        message = BytesParser(policy=policy.default).parse(file)

    lines = []
    for header in ("Subject", "From", "To", "Date"):
        value = message.get(header)
        if value:
            lines.append(f"{header}: {value}")

    if message.is_multipart():
        for part in message.walk():
            content_type = (part.get_content_type() or "").lower()
            if content_type == "text/plain":
                payload = part.get_content()
                if payload:
                    lines.append(str(payload))
    else:
        payload = message.get_content()
        if payload:
            lines.append(str(payload))

    return "\n".join(lines)


def _extract_msg(path: str) -> str:
    try:
        import extract_msg
    except ModuleNotFoundError as exc:
        raise RuntimeError("extract-msg package is required for MSG parsing") from exc

    message = extract_msg.Message(path)
    parts = [
        f"Subject: {message.subject or ''}",
        f"From: {message.sender or ''}",
        f"To: {message.to or ''}",
        message.body or "",
    ]
    return "\n".join(parts)


def _extract_html(path: str) -> str:
    try:
        from bs4 import BeautifulSoup
    except ModuleNotFoundError as exc:
        raise RuntimeError("beautifulsoup4 package is required for HTML parsing") from exc

    with open(path, "r", encoding="utf-8", errors="ignore") as file:
        html = file.read()
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def extract_text_from_document(path: str) -> str:
    extension = Path(path).suffix.lower()

    if extension == ".pdf":
        return _extract_pdf(path)
    if extension in {".txt", ".md"}:
        return _extract_text_file(path)
    if extension == ".docx":
        return _extract_docx(path)
    if extension == ".csv":
        return _extract_csv(path)
    if extension in {".xlsx", ".xls"}:
        return _extract_excel(path)
    if extension in {".jpg", ".jpeg", ".png"}:
        return _extract_image_ocr(path)
    if extension == ".eml":
        return _extract_eml(path)
    if extension == ".msg":
        return _extract_msg(path)
    if extension in {".html", ".htm"}:
        return _extract_html(path)

    raise ValueError(f"Unsupported document type: {extension or 'unknown'}")


