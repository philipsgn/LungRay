#!/usr/bin/env python3
"""
scripts/generate_final_report_pdf.py - Publication-Grade Academic PDF Generator (Rule 9 Compliant)
==================================================================================================
Compiles reports/DSP391_Full_Thesis_Report.md into a formal, print-ready, monochrome PDF paper:
reports/output/pdf/LungRay_Final_Report_DSP391.pdf adhering strictly to:
- 100% no icons or emojis (Rule 9).
- Times New Roman typography (11pt body, 1.25 line-height, justified).
- Authentic Booktabs 3-rule tables (\\toprule, \\midrule, \\bottomrule, zero vertical lines).
- Beautiful, fully-typeset mathematical formulas (zero raw LaTeX $ ... $ syntax).
- Zero horizontal divider lines (no <hr> or ---).
- Strict page-break governance (no orphan headers or table rows).
"""
import base64
import os
import re
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

import markdown


def image_to_base64_data_uri(image_path: Path) -> str:
    """Read an image file and return a base64 data URI string."""
    if not image_path.exists():
        return ""
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_academic_math(text: str) -> str:
    """
    Renders LaTeX math formulas into publication-grade HTML/Unicode typography.
    Eradicates raw '$ ... $' syntax while preserving mathematical exactness.
    """
    # 1. Block Equations ($$ ... $$)
    def _replace_block_eq(match):
        eq = match.group(1).strip()
        # Common block equations
        if "L_{total}" in eq or "L_\\text{total}" in eq or "\\mathcal{L}_{\\text{total}}" in eq:
            return (
                '<div class="equation-block">'
                '<span class="equation-text"><i>L</i><sub>total</sub> = '
                '<span class="fraction"><span class="numerator">1</span><span class="denominator"><i>B</i></span></span> '
                '&sum;<sub><i>i</i>=1</sub><sup><i>B</i></sup> &sum;<sub><i>k</i> &isin; {<i>A</i>, <i>B</i>, <i>C</i>}</sub> '
                '&#x1D7D9;(<i>t</i><sub><i>i</i></sub> = <i>k</i>) &middot; &lambda;<sub><i>k</i></sub> &middot; '
                '<i>L</i><sub><i>k</i></sub>(<i>&ycirc;</i><sub><i>i,k</i></sub>, <i>y</i><sub><i>i,k</i></sub>)</span>'
                '<span class="equation-num">(2)</span>'
                '</div>'
            )
        if "L_{ASL}" in eq or "\\mathcal{L}_{\\text{ASL}}" in eq:
            return (
                '<div class="equation-block">'
                '<span class="equation-text"><i>L</i><sub>ASL</sub> = '
                '&sum;<sub><i>c</i>=1</sub><sup>14</sup> &minus;<i>y</i><sub><i>c</i></sub> (1 &minus; <i>p</i><sub><i>c</i></sub>)<sup>&gamma;<sub>+</sub></sup> log(<i>p</i><sub><i>c</i></sub>) '
                '&minus; (1 &minus; <i>y</i><sub><i>c</i></sub>) (<i>p</i><sub><i>c,m</i></sub>)<sup>&gamma;<sub>&minus;</sub></sup> log(1 &minus; <i>p</i><sub><i>c,m</i></sub>)</span>'
                '<span class="equation-num">(3)</span>'
                '</div>'
            )
        if "\\tau_c^*" in eq:
            return (
                '<div class="equation-block">'
                '<span class="equation-text">&tau;<sub><i>c</i></sub><sup>*</sup> = '
                'arg max<sub>&tau;</sub> [ Sensitivity<sub><i>c</i></sub>(&tau;) + Specificity<sub><i>c</i></sub>(&tau;) &minus; 1 ]</span>'
                '<span class="equation-num">(4)</span>'
                '</div>'
            )
        if "E(x; T)" in eq or "E(x;" in eq:
            return (
                '<div class="equation-block">'
                '<span class="equation-text"><i>E</i>(<i>x</i>; <i>T</i>) = &minus;<i>T</i> &middot; '
                'log &sum;<sub><i>c</i></sub> exp( <sup><i>f</i><sub><i>c</i></sub>(<i>x</i>)</sup>&frasl;<sub><i>T</i></sub> )</span>'
                '<span class="equation-num">(5)</span>'
                '</div>'
            )
        if "L_{leak}" in eq or "\\mathcal{L}_{leak}" in eq:
            return (
                '<div class="equation-block">'
                '<span class="equation-text"><i>L</i><sub>leak</sub> = '
                '<span class="fraction"><span class="numerator">1</span><span class="denominator"><i>B</i></span></span> '
                '&sum;<sub><i>b</i></sub> max(0, (1 &minus; &delta;) &minus; '
                '<sup>&sum; CAM<sub><i>ij</i></sub> <i>M</i><sub>gt,<i>ij</i></sub></sup>&frasl;<sub>&sum; CAM<sub><i>ij</i></sub> + &epsilon;</sub>)</span>'
                '<span class="equation-num">(6)</span>'
                '</div>'
            )
        if "L_{cov}" in eq or "\\mathcal{L}_{cov}" in eq:
            return (
                '<div class="equation-block">'
                '<span class="equation-text"><i>L</i><sub>cov</sub> = '
                '<span class="fraction"><span class="numerator">1</span><span class="denominator"><i>B</i></span></span> '
                '&sum;<sub><i>b</i></sub> max(0, &tau;<sub><i>d</i></sub> &minus; '
                '<sup>&sum; &sigma;(10(CAM<sub><i>ij</i></sub> &minus; &theta;)) <i>M</i><sub>gt,<i>ij</i></sub></sup>&frasl;<sub>&sum; <i>M</i><sub>gt,<i>ij</i></sub> + &epsilon;</sub>)</span>'
                '<span class="equation-num">(7)</span>'
                '</div>'
            )
        return f'<div class="equation-block"><span class="equation-text"><i>{eq}</i></span></div>'

    text = re.sub(r'\$\$(.*?)\$\$', _replace_block_eq, text, flags=re.DOTALL)

    # 2. Specific inline replacements
    replacements = [
        (r'\$X \\in \\mathbb\{R\}\^\{3 \\times H \\times W\}\$', '<i>X</i> &isin; &#8477;<sup>3 &times; <i>H</i> &times; <i>W</i></sup>'),
        (r'\$H = W = 512\$', '<i>H</i> = <i>W</i> = 512'),
        (r'\$\\hat\{Y\} = \\{\\hat\{y\}_A, \\hat\{y\}_B, \\hat\{y\}_C\\}\$', '<i>&Ycirc;</i> = {<i>&ycirc;</i><sub><i>A</i></sub>, <i>&ycirc;</i><sub><i>B</i></sub>, <i>&ycirc;</i><sub><i>C</i></sub>}'),
        (r'\$\\hat\{y\}_A \\in \[0, 1\]\^\{14\}\$', '<i>&ycirc;</i><sub><i>A</i></sub> &isin; [0, 1]<sup>14</sup>'),
        (r'\$\\hat\{y\}_B \\in \[0, 1\]\$', '<i>&ycirc;</i><sub><i>B</i></sub> &isin; [0, 1]'),
        (r'\$\\hat\{y\}_C \\in \[0, 1\]\$', '<i>&ycirc;</i><sub><i>C</i></sub> &isin; [0, 1]'),
        (r'\$\\tau_c\^\\*\$', '&tau;<sub><i>c</i></sub><sup>*</sup>'),
        (r'\$\\tau_c\$', '&tau;<sub><i>c</i></sub>'),
        (r'\$\\tau_B = 0\.448\$', '&tau;<sub><i>B</i></sub> = 0.448'),
        (r'\$\\tau_C = 0\.512\$', '&tau;<sub><i>C</i></sub> = 0.512'),
        (r'\$\\tau_d\$', '&tau;<sub><i>d</i></sub>'),
        (r'\$\\ge 18\$', '&ge; 18'),
        (r'\$\\ge 80\\%\$', '&ge; 80%'),
        (r'\$\\ge 0\.80\$', '&ge; 0.80'),
        (r'\$\\ge 0\.90\$', '&ge; 0.90'),
        (r'\$\\le 2\.0\$s', '&le; 2.0s'),
        (r'\$\\Delta \\ge \+0\.02\$', '&Delta; &ge; +0.02'),
        (r'\$\\Delta\$', '&Delta;'),
        (r'\$25 \\times 25\$', '25 &times; 25'),
        (r'\$512 \\times 512 \\times 3\$', '512 &times; 512 &times; 3'),
        (r'\$512 \\times 512\$', '512 &times; 512'),
        (r'\$p < 0\.001\$', '<i>p</i> &lt; 0.001'),
        (r'\$seed=42\$', '<i>seed</i> = 42'),
        (r'\$\\gamma_-\$', '&gamma;<sub>&minus;</sub>'),
        (r'\$\\gamma_\+\$', '&gamma;<sub>+</sub>'),
        (r'\$m = 0\.05\$', '<i>m</i> = 0.05'),
        (r'\$m \\ge 0\$', '<i>m</i> &ge; 0'),
        (r'\$\\text\{CAM\} \\in \[0,1\]\^\{H\\times W\}\$', 'CAM &isin; [0, 1]<sup><i>H</i> &times; <i>W</i></sup>'),
        (r'\$M_\{gt\} \\in \\\{0,1\\\}\^\{H\\times W\}\$', '<i>M</i><sub>gt</sub> &isin; {0, 1}<sup><i>H</i> &times; <i>W</i></sup>'),
        (r'\$\\mathcal\{L\}_\{attn\}\$', '<i>L</i><sub>attn</sub>'),
        (r'\$\\mathcal\{L\}_\{leak\}\$', '<i>L</i><sub>leak</sub>'),
        (r'\$\\mathcal\{L\}_\{cov\}\$', '<i>L</i><sub>cov</sub>'),
        (r'\$\\beta\$', '&beta;'),
        (r'\$\\lambda_k\$', '&lambda;<sub><i>k</i></sub>'),
        (r'\$\\lambda_A = 1\.0\$', '&lambda;<sub><i>A</i></sub> = 1.0'),
        (r'\$\\lambda_B = 1\.0\$', '&lambda;<sub><i>B</i></sub> = 1.0'),
        (r'\$\\lambda_C = 1\.0\$', '&lambda;<sub><i>C</i></sub> = 1.0'),
        (r'\$\\epsilon\$', '&epsilon;'),
        (r'\$\\theta\$', '&theta;'),
        (r'\$\\sigma\$', '&sigma;'),
        (r'\$\\mu\$', '&mu;'),
    ]
    for pattern, rep in replacements:
        text = re.sub(pattern, rep, text)

    # 3. Generic fallback for any remaining $variable$
    text = re.sub(r'\$([A-Za-z0-9_+\-^*/]+)\$', r'<i>\1</i>', text)
    return text


def generate_final_pdf(
    md_path: str = "reports/DSP391_Full_Thesis_Report.md",
    pdf_path: str = "reports/output/pdf/LungRay_Final_Report_DSP391.pdf",
):
    abs_md = WORKSPACE_ROOT / md_path
    abs_pdf = WORKSPACE_ROOT / pdf_path
    temp_html = WORKSPACE_ROOT / "reports" / "temp_final_report_render.html"

    if not abs_md.exists():
        raise FileNotFoundError(f"Markdown report not found: {abs_md}")

    with open(abs_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Pre-render math formulas before markdown parsing
    md_text = render_academic_math(md_text)

    # Convert Markdown to HTML
    html_content = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

    # Prepare high-resolution base64 images
    img_map = {
        "training_curves.png": WORKSPACE_ROOT / "results" / "training_curves.png",
        "head_a_roc_curves.png": WORKSPACE_ROOT / "results" / "head_a_roc_curves.png",
        "head_b_tb_evaluation.png": WORKSPACE_ROOT / "results" / "head_b_tb_evaluation.png",
        "head_c_covid_evaluation.png": WORKSPACE_ROOT / "results" / "head_c_covid_evaluation.png",
        "shortcut_audit_summary.png": WORKSPACE_ROOT / "results" / "shortcut_audit_summary.png",
    }

    # Embed images in Chapter VI
    fig_blocks = ""
    for name, p in img_map.items():
        if p.exists():
            b64 = image_to_base64_data_uri(p)
            label = name.replace(".png", "").replace("_", " ").title()
            fig_blocks += (
                f'<div class="figure-container">'
                f'<img src="{b64}" alt="{label}" style="max-width: 90%; border: 1px solid #000;" />'
                f'<p class="caption"><strong>Figure.</strong> {label} generated by the LungRay evaluation pipeline.</p>'
                f'</div>'
            )

    # Academic Monochrome HTML/CSS (Rule 9 Compliant)
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>LungRay DSP391 Final Graduation Thesis Report</title>
<style>
    @page {{
        size: A4;
        margin: 22mm 20mm 22mm 20mm;
        @bottom-center {{
            content: counter(page);
            font-family: 'Times New Roman', Times, serif;
            font-size: 10pt;
        }}
    }}
    body {{
        font-family: 'Times New Roman', Times, serif;
        font-size: 11pt;
        line-height: 1.25;
        color: #000000;
        background-color: #ffffff;
        text-align: justify;
        margin: 0;
        padding: 0;
    }}
    /* Zero horizontal rules (Rule 9 & User Directive) */
    hr {{
        display: none !important;
    }}
    /* Page Break Hierarchy */
    h1 {{
        page-break-before: always;
        font-size: 16pt;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0;
        padding-top: 10pt;
        margin-bottom: 12pt;
        line-height: 1.25;
        font-weight: bold;
        page-break-after: avoid;
    }}
    /* Suppress page break on first heading */
    body > h1:first-of-type {{
        page-break-before: avoid;
    }}
    h2 {{
        font-size: 13pt;
        text-transform: uppercase;
        border-bottom: 1.5px solid #000000;
        padding-bottom: 2pt;
        margin-top: 14pt;
        margin-bottom: 6pt;
        font-weight: bold;
        page-break-after: avoid;
    }}
    h3 {{
        font-size: 11.5pt;
        margin-top: 10pt;
        margin-bottom: 4pt;
        font-weight: bold;
        font-style: italic;
        page-break-after: avoid;
    }}
    p {{
        margin-top: 0;
        margin-bottom: 6pt;
        text-indent: 1.5em;
    }}
    p.no-indent, .figure-container p, .caption, table p, blockquote p, ul p, ol p {{
        text-indent: 0;
    }}
    ul, ol {{
        margin-top: 2pt;
        margin-bottom: 6pt;
        padding-left: 20pt;
    }}
    li {{
        margin-bottom: 2pt;
        line-height: 1.2;
    }}
    strong {{
        font-weight: bold;
    }}
    em {{
        font-style: italic;
    }}
    /* Authentic Booktabs Table Styling */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 8pt;
        margin-bottom: 12pt;
        font-size: 9.5pt;
        line-height: 1.2;
        page-break-inside: auto;
    }}
    thead tr th {{
        border-top: 1.5pt solid #000000;
        border-bottom: 1.0pt solid #000000;
        padding: 5pt 4pt;
        text-align: left;
        font-weight: bold;
        background-color: #f7f7f7;
    }}
    tbody tr td {{
        padding: 4.5pt 4pt;
        border-top: none;
        border-bottom: none;
    }}
    tbody tr:last-child td {{
        border-bottom: 1.5pt solid #000000;
    }}
    tr {{
        page-break-inside: avoid;
    }}
    /* Mathematical Equation Styling */
    .equation-block {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 8pt 0;
        font-size: 11pt;
        font-style: italic;
        position: relative;
        text-align: center;
    }}
    .equation-text {{
        margin: 0 auto;
    }}
    .equation-num {{
        position: absolute;
        right: 10pt;
        font-style: normal;
        font-size: 10.5pt;
    }}
    .fraction {{
        display: inline-block;
        vertical-align: middle;
        text-align: center;
        padding: 0 2pt;
    }}
    .numerator {{
        display: block;
        border-bottom: 1px solid #000;
        padding-bottom: 1pt;
    }}
    .denominator {{
        display: block;
        padding-top: 1pt;
    }}
    .figure-container {{
        text-align: center;
        margin: 14pt 0;
        page-break-inside: avoid;
    }}
    .caption {{
        font-size: 9.5pt;
        text-align: justify;
        margin-top: 5pt;
        font-style: normal;
    }}
    pre, code {{
        font-family: 'Courier New', Courier, monospace;
        font-size: 8.5pt;
        background-color: #f9f9f9;
    }}
    pre {{
        border: 1px solid #cccccc;
        padding: 6pt;
        margin: 8pt 0;
        white-space: pre-wrap;
    }}
</style>
</head>
<body>
{html_content}
</body>
</html>
"""

    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"[*] Generated rendered HTML at: {temp_html}")

    # Headless Edge candidates
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    edge_bin = next((p for p in edge_paths if os.path.exists(p)), "msedge")

    cmd = [
        edge_bin,
        "--headless",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={abs_pdf}",
        str(temp_html.resolve().as_uri()),
    ]

    print(f"[*] Compiling publication-grade PDF via Headless Edge...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if abs_pdf.exists() and abs_pdf.stat().st_size > 50000:
            size_kb = abs_pdf.stat().st_size / 1024
            print(f"[OK] Successfully compiled PDF: {abs_pdf} ({size_kb:.1f} KB)")
            alt_pdf = WORKSPACE_ROOT / "reports" / "FINAL_SCIENTIFIC_REPORT.pdf"
            import shutil
            shutil.copyfile(abs_pdf, alt_pdf)
            print(f"[OK] Synchronized copy to: {alt_pdf} ({size_kb:.1f} KB)")
        else:
            print(f"[!] Warning: PDF generation failed or empty. Stderr: {result.stderr}")
    finally:
        if temp_html.exists():
            try:
                temp_html.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    generate_final_pdf()
