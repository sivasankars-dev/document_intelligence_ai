def extract_text_from_document(path: str) -> str:
    text_content = ""
    if path.endswith(".pdf"):
        import fitz
        doc = fitz.open(path)
        for page in doc:
            text_content += page.get_text()
    else:
        with open(path, "r") as f:
            text_content = f.read()

    return text_content



