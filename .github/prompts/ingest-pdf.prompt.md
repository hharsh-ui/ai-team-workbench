---
description: Turn a PDF into a source pack and summarize it as the source of truth (pages, pictures, tables, formulas, warnings)
agent: ProductManager
argument-hint: Path to the PDF file
---

Follow the pdf-source-of-truth skill for the PDF the user named after this command (if none, ask for the path).

1. Build the source pack with `python scripts/wb.py call pdf_source_pack pdf_path="<path>"`. For a long PDF (more than about 50 pages), ask which chapters matter and add `pages=<range>`, for example `pages=1-40`.
2. Read `INDEX.md` and report: pages, pictures, tables, numbers indexed, pages needing a transcript, and every warning with what it means.
3. If pages that matter have no text or an unreadable text layer, say how many, then transcribe them from their page images (or propose OCR) as the skill describes.
4. Check the pages that matter against their page images, and list the formulas you found (with page references).
5. Give a one-page summary of what the document says, with citations, and ask what the user wants to build or write from it.
