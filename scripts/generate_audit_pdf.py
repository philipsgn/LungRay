r"""
LungRay Academic PDF Report Generator
====================================
Converts reports/SHORTCUT_LEARNING_AUDIT_REPORT.md into a formal, publication-grade
monochrome PDF report (reports/SHORTCUT_LEARNING_AUDIT_REPORT.pdf).

Strict adherence to Rule 9:
- 100% no icons or emojis
- Formal Times New Roman typography (11pt, justified)
- Booktabs 3-rule tables (\toprule, \midrule, \bottomrule)
- Monochrome styling (black, white, grayscale)
- Headless Edge print-to-pdf with native A4 pagination
"""
from __future__ import annotations

import base64
import os
import re
import subprocess
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

import markdown


def convert_report_to_pdf(
    md_path: str = "reports/SHORTCUT_LEARNING_AUDIT_REPORT.md",
    pdf_path: str = "reports/SHORTCUT_LEARNING_AUDIT_REPORT.pdf",
    plot_path: str = "results/shortcut_audit_comparison.png",
):
    abs_md = WORKSPACE_ROOT / md_path
    abs_pdf = WORKSPACE_ROOT / pdf_path
    abs_plot = WORKSPACE_ROOT / plot_path
    temp_html = WORKSPACE_ROOT / "reports" / "temp_report_render.html"

    if not abs_md.exists():
        raise FileNotFoundError(f"Markdown report not found: {abs_md}")

    print(f"[*] Reading markdown source: {abs_md}")
    with open(abs_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    # In-line base64 plot if reference exists
    if abs_plot.exists():
        with open(abs_plot, "rb") as img_f:
            b64_data = base64.b64encode(img_f.read()).decode("utf-8")
        
        # Replace image links with responsive embedded img tag
        def img_replacer(match):
            alt = match.group(1)
            return (
                f'<div class="figure-box">'
                f'<img src="data:image/png;base64,{b64_data}" alt="{alt}" style="width: 100%; max-width: 100%; height: auto; border: 1pt solid #333333;" />'
                f'<p class="figure-caption"><strong>Hình 1.</strong> {alt}</p>'
                f'</div>'
            )
        md_text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', img_replacer, md_text)

    # Convert Markdown to HTML
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )

    # Strict Academic Monochrome CSS (Rule 9)
    academic_css = """
    @page {
        size: A4 portrait;
        margin: 20mm 15mm 20mm 15mm;
        @bottom-center {
            content: counter(page);
            font-family: "Times New Roman", Times, serif;
            font-size: 10pt;
            color: #000000;
        }
    }
    
    body {
        font-family: "Times New Roman", Times, serif;
        font-size: 11pt;
        line-height: 1.45;
        color: #000000;
        background-color: #ffffff;
        text-align: justify;
        margin: 0;
        padding: 0;
    }

    h1 {
        font-size: 16pt;
        font-weight: bold;
        text-align: center;
        text-transform: uppercase;
        margin-top: 0;
        margin-bottom: 4px;
        letter-spacing: 0.5px;
        color: #000000;
    }

    h2 {
        font-size: 12pt;
        font-weight: bold;
        text-align: center;
        margin-top: 0;
        margin-bottom: 16px;
        color: #333333;
    }

    h3 {
        font-size: 11.5pt;
        font-weight: bold;
        margin-top: 16px;
        margin-bottom: 6px;
        border-bottom: 0.75pt solid #000000;
        padding-bottom: 2px;
        color: #000000;
    }

    h4 {
        font-size: 11pt;
        font-weight: bold;
        font-style: italic;
        margin-top: 12px;
        margin-bottom: 4px;
        color: #000000;
    }

    p {
        margin-top: 0;
        margin-bottom: 8px;
        text-indent: 1.5em;
    }

    ul, ol {
        margin-top: 0;
        margin-bottom: 8px;
        padding-left: 2em;
    }

    li {
        margin-bottom: 3px;
    }

    /* Booktabs 3-Rule Academic Tables */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 14px 0 16px 0;
        font-size: 10pt;
        border-top: 1.5pt solid #000000;
        border-bottom: 1.5pt solid #000000;
    }

    thead th {
        border-bottom: 1pt solid #000000;
        padding: 6px 6px;
        font-weight: bold;
        text-align: left;
        color: #000000;
    }

    tbody td {
        padding: 5px 6px;
        border-top: none;
        border-bottom: none;
        color: #000000;
    }

    tbody tr:last-child td {
        border-bottom: 1.5pt solid #000000;
    }

    .table-caption {
        font-size: 10pt;
        font-weight: bold;
        margin-bottom: 4px;
        text-align: left;
    }

    .figure-box {
        margin: 16px 0;
        text-align: center;
        page-break-inside: avoid;
    }

    .figure-caption {
        font-size: 9.5pt;
        font-style: italic;
        margin-top: 6px;
        text-align: center;
        text-indent: 0;
    }

    hr {
        border: none;
        border-top: 0.5pt solid #888888;
        margin: 14px 0;
    }

    blockquote {
        margin: 10px 0;
        padding: 6px 12px;
        border-left: 2.5pt solid #333333;
        background-color: #f7f7f7;
        font-style: italic;
    }

    code {
        font-family: "Courier New", Courier, monospace;
        font-size: 9.5pt;
        background-color: #f0f0f0;
        padding: 1px 3px;
    }
    """

    full_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Short-cut Learning Audit Report</title>
    <style>
    {academic_css}
    </style>
</head>
<body>
    {html_body}
</body>
</html>
"""

    print(f"[*] Writing temporary HTML render to: {temp_html}")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(full_html)

    # Locate Microsoft Edge executable
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe"),
    ]
    edge_bin = next((p for p in edge_paths if os.path.exists(p)), None)

    if not edge_bin:
        raise RuntimeError("Microsoft Edge executable not found for PDF printing.")

    print(f"[*] Compiling PDF via Headless Edge: {edge_bin}")
    os.makedirs(abs_pdf.parent, exist_ok=True)
    temp_uri = temp_html.resolve().as_uri()
    cmd = [
        edge_bin,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        f"--print-to-pdf={abs_pdf}",
        "--no-pdf-header-footer",
        temp_uri,
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    if res.returncode != 0:
        raise RuntimeError(f"Edge PDF print failed: {res.stderr.decode('utf-8', errors='ignore')}")

    # Remove temporary HTML (Rule 8: Lean Workspace)
    if temp_html.exists():
        temp_html.unlink()

    pdf_size = abs_pdf.stat().st_size
    print(f"[+] Successfully generated Academic PDF: {abs_pdf} ({pdf_size:,} bytes)")
    return abs_pdf


if __name__ == "__main__":
    convert_report_to_pdf()
