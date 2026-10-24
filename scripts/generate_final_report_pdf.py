r"""
LungRay Final Scientific Report PDF Compiler (Rule 9 Compliant)
================================================================
Converts reports/FINAL_SCIENTIFIC_REPORT.md into a publication-grade
monochrome PDF paper: reports/FINAL_SCIENTIFIC_REPORT.pdf (20-25 pages equivalent).

Strict Rule 9 Adherence:
- 100% no icons or emojis
- Times New Roman typography (11pt body, 1.35 line-height, text-align: justify)
- Booktabs 3-rule tables (\toprule, \midrule, \bottomrule)
- Monochrome styling (black, white, grayscale)
- Embedded high-resolution figures from results/
- Headless Edge print-to-pdf engine
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


def generate_final_pdf(
    md_path: str = "reports/FINAL_SCIENTIFIC_REPORT.md",
    pdf_path: str = "reports/FINAL_SCIENTIFIC_REPORT.pdf",
    arch_png: str = "results/figures/architecture_radar_comparison.png",
    audit_png: str = "results/shortcut_audit_comparison.png",
):
    abs_md = WORKSPACE_ROOT / md_path
    abs_pdf = WORKSPACE_ROOT / pdf_path
    abs_arch_png = WORKSPACE_ROOT / arch_png
    abs_audit_png = WORKSPACE_ROOT / audit_png
    temp_html = WORKSPACE_ROOT / "reports" / "temp_final_report_render.html"

    if not abs_md.exists():
        raise FileNotFoundError(f"Markdown report not found: {abs_md}")

    with open(abs_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Convert Markdown to HTML with tables extension
    html_content = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

    # Prepare base64 images
    arch_b64 = image_to_base64_data_uri(abs_arch_png)
    audit_b64 = image_to_base64_data_uri(abs_audit_png)

    # Insert Figures into corresponding sections
    figure1_html = f"""
    <div class="figure-container">
        <img src="{arch_b64}" alt="Figure 1: Architectural Comparison" style="max-width: 100%; border: 1px solid #000;" />
        <p class="caption"><strong>Figure 1.</strong> Empirical Architectural Benchmark across DenseNet-121, ResNet-50, and ViT-B/16 on 512x512 chest radiographs, illustrating (a) Parameter complexity, (b) Inference latency per image, and (c) Multi-task macro AUROC.</p>
    </div>
    """

    figure2_html = f"""
    <div class="figure-container">
        <img src="{audit_b64}" alt="Figure 2: Pulmonary Grounding Shortcut Audit" style="max-width: 100%; border: 1px solid #000;" />
        <p class="caption"><strong>Figure 2.</strong> In-Lung Activation Energy Distribution across 150 COVID-19 Test Cases under (1) Unmasked Baseline, (2) Input Masking Only, and (3) Clinical Pulmonary Grounding, demonstrating complete suppression of non-physiological shortcut confounders (p = 1.15e-26).</p>
    </div>
    """

    # Replace section markers or append figures
    if "### 5.2. Experiment 2: Architectural Arena" in html_content:
        html_content = html_content.replace(
            "### 5.2. Experiment 2: Architectural Arena",
            figure1_html + "\n### 5.2. Experiment 2: Architectural Arena"
        )
    else:
        html_content += figure1_html

    if "### 5.5. Experiment 5: Pulmonary Grounding Audit" in html_content:
        html_content = html_content.replace(
            "### 5.5. Experiment 5: Pulmonary Grounding Audit",
            figure2_html + "\n### 5.5. Experiment 5: Pulmonary Grounding Audit"
        )
    else:
        html_content += figure2_html

    # Academic Monochrome CSS
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>LungRay Scientific Monograph</title>
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
        line-height: 1.35;
        color: #000000;
        background-color: #ffffff;
        text-align: justify;
        margin: 0;
        padding: 0;
    }}
    h1 {{
        font-size: 18pt;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0;
        margin-bottom: 12pt;
        line-height: 1.25;
        font-weight: bold;
    }}
    h2 {{
        font-size: 13pt;
        text-transform: uppercase;
        border-bottom: 1.5px solid #000000;
        padding-bottom: 2pt;
        margin-top: 18pt;
        margin-bottom: 8pt;
        font-weight: bold;
    }}
    h3 {{
        font-size: 11.5pt;
        margin-top: 12pt;
        margin-bottom: 4pt;
        font-weight: bold;
        font-style: italic;
    }}
    p {{
        margin-top: 0;
        margin-bottom: 8pt;
        text-indent: 1.5em;
    }}
    p.no-indent, .figure-container p, .caption, table p, blockquote p {{
        text-indent: 0;
    }}
    strong {{
        font-weight: bold;
    }}
    em {{
        font-style: italic;
    }}
    /* Booktabs table styling */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 12pt;
        margin-bottom: 14pt;
        font-size: 9.5pt;
        line-height: 1.2;
    }}
    thead th {{
        border-top: 2px solid #000000;
        border-bottom: 1px solid #000000;
        padding: 5pt 4pt;
        text-align: left;
        font-weight: bold;
    }}
    tbody td {{
        padding: 4pt 4pt;
        border-bottom: 0.5px solid #e0e0e0;
    }}
    tbody tr:last-child td {{
        border-bottom: 2px solid #000000;
        font-weight: bold;
    }}
    .figure-container {{
        text-align: center;
        margin: 16pt 0;
        page-break-inside: avoid;
    }}
    .caption {{
        font-size: 9.5pt;
        text-align: justify;
        margin-top: 6pt;
        font-style: normal;
    }}
    pre, code {{
        font-family: 'Courier New', Courier, monospace;
        font-size: 8.5pt;
        background-color: #f7f7f7;
    }}
    pre {{
        border: 1px solid #cccccc;
        padding: 6pt;
        margin: 8pt 0;
        white-space: pre-wrap;
    }}
    hr {{
        border: 0;
        border-top: 1px solid #000000;
        margin: 14pt 0;
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
    print(f"[*] Generated HTML rendered report at: {temp_html}")

    # Edge Path candidates on Windows
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    edge_bin = next((p for p in edge_paths if os.path.exists(p)), "msedge")

    cmd = [
        edge_bin,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={abs_pdf}",
        str(temp_html.resolve().as_uri()),
    ]

    print(f"[*] Compiling publication-grade PDF via Headless Edge...")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if abs_pdf.exists() and abs_pdf.stat().st_size > 50000:
        size_kb = abs_pdf.stat().st_size / 1024
        print(f"[OK] Successfully compiled: {abs_pdf} ({size_kb:.1f} KB)")
        # Clean up temporary HTML file (Rule 8: Lean Workspace)
        if temp_html.exists():
            temp_html.unlink()
    else:
        print(f"[!] Warning: PDF generation failed or empty. Stderr: {result.stderr}")


if __name__ == "__main__":
    generate_final_pdf()
