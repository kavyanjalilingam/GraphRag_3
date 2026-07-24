from __future__ import annotations

import csv
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


def load_questions(path: str | Path) -> list[dict[str, Any]]:
    """Load Round 3 questions from CSV, JSON, or DOCX.

    CSV/JSON format should contain at least:
      - question_id
      - question_text

    DOCX parsing is best-effort and is intended for the official question document.
    """
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("questions"), list):
            return data["questions"]
        raise ValueError("JSON question file must contain a list or a top-level 'questions' list.")

    if suffix == ".csv":
        with p.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            return [dict(row) for row in reader]

    if suffix == ".docx":
        return parse_docx_questions(p)

    raise ValueError(f"Unsupported question file type: {suffix}")


def parse_docx_questions(path: Path) -> list[dict[str, Any]]:
    """Best-effort parser for a DOCX question list.

    It extracts paragraphs from the Word XML and heuristically groups them into
    question records when the text looks like an official evaluation question.
    """
    with zipfile.ZipFile(path) as zf:
        xml_bytes = zf.read("word/document.xml")

    root = ET.fromstring(xml_bytes)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2000/main"}

    paragraphs: list[str] = []
    for para in root.findall(".//w:p", ns):
        texts = [node.text for node in para.findall(".//w:t", ns) if node.text]
        text = "".join(texts).strip()
        if text:
            paragraphs.append(text)

    questions: list[dict[str, Any]] = []
    current_id = None
    current_text: list[str] = []

    for para in paragraphs:
        if re.fullmatch(r"EQ\d+", para.strip()):
            if current_id is not None and current_text:
                questions.append({
                    "question_id": current_id,
                    "question_text": " ".join(current_text).strip(),
                })
            current_id = para.strip()
            current_text = []
            continue

        if current_id is not None:
            current_text.append(para)

    if current_id is not None and current_text:
        questions.append({
            "question_id": current_id,
            "question_text": " ".join(current_text).strip(),
        })

    return questions
