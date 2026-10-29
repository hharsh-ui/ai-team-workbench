"""Source-of-truth tools: turn a PDF into a source pack, and check that numbers come from it."""

from agent_workbench.services import pdf_pack


def pdf_source_pack(pdf_path: str, out_dir: str = "", pages: str = "", page_dpi: int = 150, image_dpi: int = 200, force: bool = False) -> dict:
    """Turn a PDF into a source pack (default folder: sources/<pdf-name>/): page images, text, tables as CSV, figure crops, original images, a numbers index and warnings. Pages with no or unreadable text are flagged for a transcript from the page image. pages limits the pack, for example 1-5,8 (default: all). Needs: pip install pdfplumber. force=true rebuilds an existing pack."""
    return {"success": True, **pdf_pack.build_source_pack(pdf_path, out_dir, page_dpi, image_dpi, force, pages)}


def source_check_numbers(pack_dir: str, text_file: str, min_digits: int = 2) -> dict:
    """List the numbers in text_file that are not in the source pack (numbers.csv and checked transcripts). A number followed by a unit (2 g, 6 volt, 10 EUR) must match with its unit. Citations such as [source p.12] are ignored. Each missing number must be calculated by code or corrected."""
    result = pdf_pack.check_numbers(pack_dir, text_file, min_digits)
    return {"success": True, **result}
