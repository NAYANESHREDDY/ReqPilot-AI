import re
from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader
import docx

class IngestionAgent:
    """Agent 8.2: Document Ingestion Agent
    Accepts PDF, DOCX, TXT, Markdown; extracts text; preserves document/page/section metadata;
    chunks content and stores source provenance.
    """

    def parse_file(self, file_path: Path, filename: str) -> List[Dict[str, Any]]:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return self._parse_pdf(file_path, filename)
        elif ext in [".docx", ".doc"]:
            return self._parse_docx(file_path, filename)
        else:
            return self._parse_text(file_path, filename)

    def _parse_pdf(self, file_path: Path, filename: str) -> List[Dict[str, Any]]:
        chunks = []
        reader = PdfReader(str(file_path))
        chunk_idx = 0

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                continue

            sections = self._split_into_sections(text)
            for sec_title, sec_text in sections:
                if sec_text.strip():
                    chunk_idx += 1
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "section_title": sec_title,
                        "page_number": page_num,
                        "content": sec_text.strip(),
                        "token_count": len(sec_text.split()),
                    })
        return chunks

    def _parse_docx(self, file_path: Path, filename: str) -> List[Dict[str, Any]]:
        chunks = []
        doc = docx.Document(str(file_path))
        current_section = "Introduction"
        current_text = []
        chunk_idx = 0
        approx_page = 1
        para_count = 0

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            para_count += 1
            if para_count % 15 == 0:
                approx_page += 1

            if para.style.name.startswith("Heading") or (len(text) < 80 and text.endswith((":"))):
                if current_text:
                    chunk_idx += 1
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "section_title": current_section,
                        "page_number": approx_page,
                        "content": "\n".join(current_text),
                        "token_count": sum(len(t.split()) for t in current_text),
                    })
                    current_text = []
                current_section = text
            else:
                current_text.append(text)

        if current_text:
            chunk_idx += 1
            chunks.append({
                "chunk_index": chunk_idx,
                "section_title": current_section,
                "page_number": approx_page,
                "content": "\n".join(current_text),
                "token_count": sum(len(t.split()) for t in current_text),
            })

        return chunks

    def _parse_text(self, file_path: Path, filename: str) -> List[Dict[str, Any]]:
        chunks = []
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        sections = self._split_into_sections(content)
        chunk_idx = 0
        approx_page = 1

        for i, (sec_title, sec_text) in enumerate(sections):
            if sec_text.strip():
                chunk_idx += 1
                approx_page = (chunk_idx // 3) + 1
                chunks.append({
                    "chunk_index": chunk_idx,
                    "section_title": sec_title,
                    "page_number": approx_page,
                    "content": sec_text.strip(),
                    "token_count": len(sec_text.split()),
                })
        return chunks

    def _split_into_sections(self, text: str) -> List[tuple]:
        lines = text.splitlines()
        sections = []
        current_title = "Overview"
        current_lines = []

        for line in lines:
            line_str = line.strip()
            # Detect headings like # Heading or 1.2 Title or CAPITALIZED
            if (line_str.startswith("#") or
                re.match(r"^\d+(\.\d+)*\s+[A-Z]", line_str) or
                (len(line_str) < 60 and line_str.isupper() and len(line_str) > 3)):
                if current_lines:
                    sections.append((current_title, "\n".join(current_lines)))
                    current_lines = []
                current_title = line_str.lstrip("#").strip()
            else:
                if line_str:
                    current_lines.append(line_str)

        if current_lines:
            sections.append((current_title, "\n".join(current_lines)))

        if not sections:
            sections = [("Overview", text)]

        return sections
