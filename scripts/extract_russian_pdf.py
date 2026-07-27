from pathlib import Path
from pypdf import PdfReader

root = Path(__file__).resolve().parents[1]
pdf = root / "source-russkiy" / "ege-2026-russkiy-demoversiya.pdf"
out = root / "scripts" / "russian_pdf_text.txt"
reader = PdfReader(str(pdf))
parts = []
for index, page in enumerate(reader.pages, start=1):
    parts.append(f"\n===== PDF PAGE {index} =====\n")
    parts.append(page.extract_text() or "")
out.write_text("\n".join(parts), encoding="utf-8", newline="\n")
print(f"Extracted {len(reader.pages)} pages")
