"""XML text extraction preserving logical node order."""

from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


def extract_clean_text(xml_path: str | Path) -> str:
    root = ET.parse(xml_path).getroot()
    chunks: list[str] = []
    for text in root.itertext():
        normalized = " ".join(text.split())
        if normalized:
            chunks.append(normalized)
    return " ".join(chunks)
