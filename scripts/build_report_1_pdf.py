#!/usr/bin/env python3
"""
scripts/build_report_1_pdf.py - Build Publication-Grade PDF for Report #1 (Project Proposal)
Adheres strictly to Rule 9 (Academic Report Standards):
- Font: TrueType Times New Roman from Windows Fonts (Full Unicode & Typography).
- Tables: Authentic Booktabs style (top/bottom thick rules, header divider, zero vertical lines).
- Output: reports/output/pdf/LungRay_Report_1_Project_Proposal.pdf
"""
import os
import sys
from pathlib import Path
from fpdf import FPDF

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

class AcademicReportPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(left=20, top=20, right=20)
        
        # Register TrueType Times New Roman for full Unicode support
        self.add_font("TimesNR", "", r"C:\Windows\Fonts\times.ttf")
        self.add_font("TimesNR", "B", r"C:\Windows\Fonts\timesbd.ttf")
        self.add_font("TimesNR", "I", r"C:\Windows\Fonts\timesi.ttf")
        self.add_font("TimesNR", "BI", r"C:\Windows\Fonts\timesbi.ttf")

    def header(self):
        if self.page_no() > 1:
            self.set_font("TimesNR", "I", 8.5)
            self.set_text_color(90, 90, 90)
            self.cell(0, 6, "DSP391 Capstone Project Proposal — LungRay Platform | Group 11", border=0, align="L")
            self.ln(3)
            self.set_draw_color(180, 180, 180)
            self.set_line_width(0.2)
            self.line(self.get_x(), self.get_y(), self.get_x() + 170, self.get_y())
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("TimesNR", "I", 8.5)
        self.set_text_color(100, 100, 100)
        self.set_draw_color(180, 180, 180)
        self.set_line_width(0.2)
        self.line(20, self.get_y() - 2, 190, self.get_y() - 2)
        self.cell(100, 8, "Department of Computer Science — FPT University", border=0, align="L")
        self.cell(70, 8, f"Page {self.page_no()}", border=0, align="R")

    def chapter_title(self, title):
        self.set_font("TimesNR", "B", 13.0)
        self.set_text_color(0, 0, 0)
        self.ln(4)
        self.cell(0, 7, title, border=0, align="L")
        self.ln(6)
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.6)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(4)

    def section_title(self, title):
        self.set_font("TimesNR", "B", 11.0)
        self.set_text_color(0, 0, 0)
        self.ln(3)
        self.cell(0, 6, title, border=0, align="L")
        self.ln(5)

    def subsection_title(self, title):
        self.set_font("TimesNR", "B", 10.0)
        self.set_text_color(30, 30, 30)
        self.ln(2)
        self.cell(0, 5.5, title, border=0, align="L")
        self.ln(4)

    def paragraph(self, text):
        self.set_font("TimesNR", "", 9.8)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 5.0, text, align="J")
        self.ln(2.5)

    def bullet_point(self, bold_prefix, text):
        self.set_font("TimesNR", "B", 9.8)
        self.set_text_color(0, 0, 0)
        prefix = f"• {bold_prefix}: " if bold_prefix else "• "
        self.write(5.0, prefix)
        self.set_font("TimesNR", "", 9.8)
        self.set_text_color(20, 20, 20)
        self.write(5.0, text + "\n")
        self.ln(1.5)

    def table_caption(self, caption):
        self.set_font("TimesNR", "I", 8.8)
        self.set_text_color(50, 50, 50)
        self.cell(0, 5.0, caption, border=0, align="L")
        self.ln(4.0)

    def draw_booktabs_table(self, headers, rows, col_widths, col_aligns=None):
        if col_aligns is None:
            col_aligns = ["L"] * len(headers)

        self.set_draw_color(0, 0, 0)
        
        # Top Rule (Thick)
        self.set_line_width(0.6)
        x_start = self.get_x()
        y_top = self.get_y()
        total_width = sum(col_widths)
        self.line(x_start, y_top, x_start + total_width, y_top)

        # Header Row
        self.set_font("TimesNR", "B", 8.8)
        self.set_text_color(0, 0, 0)
        max_h = 6.0
        for i, h in enumerate(headers):
            self.cell(col_widths[i], max_h, h, border=0, align=col_aligns[i])
        self.ln(max_h)

        # Mid Rule (Thin)
        y_mid = self.get_y()
        self.set_line_width(0.3)
        self.line(x_start, y_mid, x_start + total_width, y_mid)

        # Body Rows
        self.set_font("TimesNR", "", 8.5)
        self.set_text_color(30, 30, 30)
        for r_idx, row in enumerate(rows):
            # Calculate row height
            row_height = 5.0
            for i, cell_val in enumerate(row):
                lines = str(cell_val).split("\n")
                row_height = max(row_height, len(lines) * 4.2 + 2)

            # Check page break
            if self.get_y() + row_height > self.page_break_trigger:
                self.add_page()
                # Redraw header on new page
                self.set_line_width(0.6)
                self.line(x_start, self.get_y(), x_start + total_width, self.get_y())
                self.set_font("TimesNR", "B", 8.8)
                for i, h in enumerate(headers):
                    self.cell(col_widths[i], 6.0, h, border=0, align=col_aligns[i])
                self.ln(6.0)
                self.set_line_width(0.3)
                self.line(x_start, self.get_y(), x_start + total_width, self.get_y())
                self.set_font("TimesNR", "", 8.5)

            y_curr = self.get_y()
            for i, cell_val in enumerate(row):
                x_curr = x_start + sum(col_widths[:i])
                self.set_xy(x_curr, y_curr)
                self.multi_cell(col_widths[i], 4.2, str(cell_val), border=0, align=col_aligns[i])

            self.set_xy(x_start, y_curr + row_height)

            # Subtle row divider
            if r_idx < len(rows) - 1:
                self.set_draw_color(220, 220, 220)
                self.set_line_width(0.15)
                self.line(x_start, self.get_y() - 0.5, x_start + total_width, self.get_y() - 0.5)
                self.set_draw_color(0, 0, 0)

        # Bottom Rule (Thick)
        self.set_line_width(0.6)
        y_bot = self.get_y()
        self.line(x_start, y_bot, x_start + total_width, y_bot)
        self.ln(5.0)


def build_proposal_pdf():
    pdf = AcademicReportPDF()
    pdf.add_page()

    # ------------------ TITLE & METADATA BANNER ------------------
    pdf.set_font("TimesNR", "B", 14.0)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6.2, "LUNGRAY: MULTI-TASK CLINICAL CADX AND TRUSTWORTHY WSOL GROUNDING PLATFORM", align="C")
    pdf.ln(2)

    pdf.set_font("TimesNR", "B", 10.0)
    pdf.cell(0, 5, "CAPSTONE PROJECT PROPOSAL (REPORT #1) — COURSE CODE: DSP391", align="C")
    pdf.ln(5)

    pdf.set_font("TimesNR", "I", 9.2)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 4.5, "Specialization: Artificial Intelligence & Data Science | Department of Computer Science", align="C")
    pdf.ln(4)
    pdf.cell(0, 4.5, "FPT University, Ho Chi Minh City Campus — November 2026", align="C")
    pdf.ln(5)

    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.8)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)

    # Metadata Block
    pdf.set_font("TimesNR", "B", 9.2)
    pdf.set_text_color(0, 0, 0)
    pdf.write(5.0, "Authorship (Group 11): ")
    pdf.set_font("TimesNR", "", 9.2)
    pdf.write(5.0, "Tan Phat (Lead AI Architect) & Manh (AI Research & Data Operations Engineer)\n")
    pdf.set_font("TimesNR", "B", 9.2)
    pdf.write(5.0, "Academic Supervisor: ")
    pdf.set_font("TimesNR", "", 9.2)
    pdf.write(5.0, "[Academic Supervisor Name] | Faculty of Computer Science & Artificial Intelligence\n")
    pdf.set_font("TimesNR", "B", 9.2)
    pdf.write(5.0, "Repository: ")
    pdf.set_font("TimesNR", "", 9.2)
    pdf.write(5.0, "https://github.com/philipsgn/LungRay.git | Schedule: 9-Week Accelerated Capstone Cycle\n")
    pdf.ln(3)

    # ------------------ CHAPTER I: PROJECT INTRODUCTION ------------------
    pdf.chapter_title("I. PROJECT INTRODUCTION")

    # 1. Overview
    pdf.section_title("1. Overview")
    pdf.subsection_title("1.1 Project Information")
    pdf.paragraph(
        "The foundational metadata, organizational structure, and clinical stakeholder definitions "
        "governing the LungRay multi-task CADx platform are systematically outlined in Table 1.1."
    )

    pdf.table_caption("Table 1.1: Project Information and Organizational Metadata.")
    t1_headers = ["Attribute", "Detailed Specification"]
    t1_rows = [
        ["Project Name", "LungRay: Multi-Task Clinical CADx and Trustworthy WSOL Grounding Platform"],
        ["Project Code", "DSP391 (System Code: DSP391-LUNGRAY-CADX-2026) | Group: Group 11"],
        ["Team Members", "Tan Phat (Lead AI Architect & Systems Engineer)\nManh (AI Research & Data Operations Engineer)"],
        ["Supervisor", "[Supervisor Name] — Department of Computer Science & AI, FPT University"],
        ["Stakeholders", "Radiologists (Triaging & Second Reader), Emergency Clinicians, Defense Committee"],
        ["Architecture", "Multi-Task 3-Head CNN (Shared DenseNet-121 Encoder, 512×512 Input Resolution)"],
        ["Clinical Scope", "16 Cardiopulmonary Conditions: 14 NIH Thoracic Diseases + Tuberculosis + COVID-19"],
        ["Safety Systems", "Helmholtz Free Energy OOD Lockout (Tau_E = 9.0421) & Multi-Scale Grad-CAM++ IoU"],
    ]
    pdf.draw_booktabs_table(t1_headers, t1_rows, [40, 130])

    pdf.subsection_title("1.2 Project Overview")
    pdf.paragraph(
        "Chest radiography (Chest X-ray, CXR) represents the most ubiquitous diagnostic projectional imaging examination "
        "in modern medicine, accounting for over 40% of all diagnostic imaging workloads globally. Radiologists inspect "
        "projectional radiographs to detect pneumonia, tuberculosis, pulmonary edema, cardiomegaly, and thoracic masses. "
        "However, healthcare institutions face an acute, compounding crisis: skyrocketing scan volumes contrasted against "
        "a worldwide shortage of board-certified radiologists. This disparity induces substantial cognitive fatigue, "
        "prolonged turnaround times (24 to 72 hours in resource-limited clinics), and diagnostic discrepancy rates "
        "between 10% and 30% in high-volume emergency triaging."
    )
    pdf.paragraph(
        "The LungRay initiative establishes an enterprise-grade Computer-Aided Diagnosis (CADx) platform to bridge this "
        "clinical gap. Moving beyond conventional single-task architectures, LungRay formulates a unified Multi-Task 3-Head "
        "Convolutional Neural Network driven by a shared DenseNet-121 visual encoder. The platform executes simultaneous, "
        "holistic screening across sixteen cardiopulmonary pathologies while enforcing Weakly-Supervised Object Localization "
        "(WSOL) via Multi-Scale Grad-CAM++ to render decisions visually and mathematically interpretable."
    )

    # 2. Project Background
    pdf.section_title("2. Project Background")
    pdf.paragraph(
        "Planar chest radiographs provide a non-invasive, high-resolution anatomical survey of the thorax. Interpreting "
        "these images represents an intricate perceptual challenge due to subtle gradations in radiopacity, overlapping "
        "cardiopulmonary shadows, and low signal-to-noise ratios. In high-prevalence infectious outbreaks (such as active "
        "tuberculosis endemic regions or viral pneumonia pandemics), delayed triaging directly leads to disease transmission "
        "and elevated patient mortality."
    )
    pdf.paragraph(
        "While deep learning has demonstrated expert-level accuracy on curated datasets, translation into clinical workflows "
        "has been obstructed by three systemic vulnerabilities:"
    )
    pdf.bullet_point(
        "Task Siloization and Memory Redundancy",
        "Prior systems train separate, disconnected neural networks for each pathology, requiring hospitals to deploy dozens "
        "of models into GPU memory, which results in unsustainable VRAM overhead and operational fragmentation."
    )
    pdf.bullet_point(
        "Extreme Positive-Negative Class Imbalance",
        "Within multi-label cohorts like NIH ChestX-ray14, positive prevalence for conditions like Hernia (0.2%) or Pneumothorax (4.7%) "
        "is heavily outnumbered by negative samples. Standard Cross-Entropy loss collapses toward majority negatives."
    )
    pdf.bullet_point(
        "Confounder Memorization (Shortcut Learning)",
        "Deep convolutional networks routinely learn non-physiological shortcuts (such as hospital-specific metal markers 'R'/'L' "
        "and detector border artifacts) rather than true pathology, resulting in failure when tested across external hospitals."
    )

    # 3. Project Objectives
    pdf.section_title("3. Project Objectives")
    pdf.paragraph(
        "The primary engineering objective is to develop, validate, and deploy an explainable, multi-task CADx system "
        "that maximizes diagnostic discrimination while enforcing clinical safety guardrails. The concrete SMART objectives comprise:"
    )
    pdf.bullet_point("Unified Multi-Task Architecture", "Construct MultiTaskChestXrayNet operating at 512×512 resolution, isolating gradients across 3 heads via parameter-free LayerNorm feature projection.")
    pdf.bullet_point("Zero Patient-Level Data Leakage", "Enforce strict patient-wise partitioning ensuring zero overlapping Patient_ID instances across train/val/test splits (70/10/20 on NIH ChestX-ray14).")
    pdf.bullet_point("Multi-Task Batch Equilibrium", "Formulate WeightedMultiTaskBatchSampler maintaining an exact ratio of 60% NIH : 25% COVIDx : 15% TB per mini-batch to prevent task starvation.")
    pdf.bullet_point("Imbalance Mitigation via Asymmetric Loss", "Implement Asymmetric Loss (ASL) with probability margin m = 0.05 to elevate minority-class multi-label ROC-AUC above 0.82 on Head A.")
    pdf.bullet_point("Trustworthy WSOL Localization", "Deploy Multi-Scale Grad-CAM++ achieving Mean Box-IoU >= 0.35 against expert radiologist bounding boxes (VinDr-CXR and RSNA) without box supervision in training.")
    pdf.bullet_point("Shortcut Learning Audit & Defeat", "Enforce automated dilated lung masking, ensuring that >= 80% of gradient activation energy resides within anatomical lung fields on COVID-19 positive radiographs.")
    pdf.bullet_point("Clinical Fail-Safe Layer", "Deploy Helmholtz Free Energy Out-of-Distribution screening to identify and reject corrupted or non-CXR inputs prior to classification.")
    pdf.bullet_point("Sub-Two-Second PACS Serving", "Containerize the platform into an asynchronous FastAPI backend delivering inference within <= 1.8 seconds, paired with a Next.js 14 Medical PACS Darkroom Viewer.")

    # 4. Problem Statement
    pdf.section_title("4. Problem Statement")
    pdf.paragraph(
        "Formally, let an input frontal chest radiograph be formalized as an image tensor X in R^(3 × 512 × 512). "
        "The multi-task CADx system maps X to a compound prediction vector Y_hat = {y_hat_A, y_hat_B, y_hat_C} "
        "parameterized by shared convolutional encoder f_theta(X):"
    )
    pdf.paragraph(
        "    • y_hat_A = sigma(g_phi_A(f_theta(X))) in [0, 1]^14  (Bernoulli probabilities for 14 NIH thoracic findings)\n"
        "    • y_hat_B = sigma(g_phi_B(f_theta(X))) in [0, 1]       (Scalar probability of active pulmonary tuberculosis)\n"
        "    • y_hat_C = Softmax(g_phi_C(f_theta(X))) in [0, 1]^3    (Probabilities for COVID-19 differential triage)"
    )
    pdf.paragraph(
        "The core technical hurdles include resolving disjoint dataset label spaces, overcoming the 98.6% negative label ratio "
        "in multi-label loss gradients, extracting multi-focal lesion boxes without spatial supervision, and preserving real-time latency."
    )

    # 5. Significance of the Project
    pdf.section_title("5. Significance of the Project")
    pdf.bullet_point(
        "Clinical Impact & Patient Outcomes",
        "Functions as an intelligent second-reader. In emergency wards, it parses incoming radiographs within two seconds, "
        "prioritizing acute conditions (Tension Pneumothorax, Massive Effusion) to the top of radiologist worklists."
    )
    pdf.bullet_point(
        "Academic & Methodological Novelty",
        "Demonstrates that multi-task parameter sharing with asymmetric loss matches or exceeds independent networks while "
        "slashing parameter footprint by 66%. Replaces subjective visual heatmap inspection with quantitative Bounding Box IoU validation."
    )
    pdf.bullet_point(
        "Economic & Healthcare Accessibility",
        "Containerized as a lightweight microservice with CPU/GPU dynamic fallback, allowing deployment on standard edge "
        "workstations in regional hospitals without high-bandwidth cloud dependency."
    )

    # 6. Project Scope & Limitations
    pdf.section_title("6. Project Scope & Limitations")
    pdf.paragraph("To guarantee safe clinical governance, explicit operational boundaries are established:")
    pdf.bullet_point("In-Scope Capabilities", "Adult frontal projection chest radiographs (PA/AP views); 16 thoracic conditions; interactive Grad-CAM++ overlays; Free Energy OOD safety screening; Next.js darkroom viewer.")
    pdf.bullet_point("Pediatric Scans Excluded", "Neonatal and pediatric thoracic anatomy differs fundamentally from adults; pediatric cohorts are strictly excluded from operational design.")
    pdf.bullet_point("Lateral Projections Excluded", "Only frontal projection radiographs are supported; lateral CXRs are outside current processing scope.")
    pdf.bullet_point("Non-Autonomous Classification", "Designed strictly as an assistive second-reader (Class IIa Medical Software); final clinical diagnosis remains the legal responsibility of certified medical doctors.")

    # 7. Preliminary Research & Proposed Technical Approach
    pdf.section_title("7. Preliminary Research & Proposed Technical Approach")
    pdf.paragraph(
        "To guarantee generalizability and prevent institutional bias, the platform curates six verified open-access "
        "benchmarks comprising over 142,000 chest radiographs (Table 1.2)."
    )

    pdf.table_caption("Table 1.2: Standardized Clinical Radiography Datasets in LungRay Platform.")
    t2_headers = ["Dataset Identifier", "Clinical Scope", "Cohort Size", "Primary Function in Project"]
    t2_rows = [
        ["NIH ChestX-ray14", "14 Thoracic Diseases", "112,120 CXRs", "Head A Multi-Label Training & Testing"],
        ["TB Radiography", "Pulmonary Tuberculosis", "7,000 CXRs", "Head B Tuberculosis Screening"],
        ["COVIDx CXR-4", "COVID-19 / Pneumonia / Normal", "16,400+ CXRs", "Head C COVID-19 Differential Triage"],
        ["VinDr-CXR", "Vietnamese Thoracic Cohort", "3,000 CXRs", "Quantitative WSOL IoU External Benchmark"],
        ["RSNA Pneumonia", "Pneumonia Consolidations", "6,000+ CXRs", "Quantitative WSOL IoU External Benchmark"],
        ["Stanford CheXpert", "External Multi-Label Cohort", "1,000 CXRs", "Out-of-Distribution Generalization Audit"],
    ]
    pdf.draw_booktabs_table(t2_headers, t2_rows, [40, 45, 30, 55])

    # 8. Project Execution Plan & Milestones
    pdf.section_title("8. Project Execution Plan & Milestones")
    pdf.paragraph(
        "The project is structured across an accelerated 9-week execution lifecycle, organized into agile sprint deliverables "
        "and verified through six formal Quality Delivery Gates (Table 1.3)."
    )

    pdf.table_caption("Table 1.3: Nine-Week Project Execution Roadmap and Quality Delivery Gates.")
    t3_headers = ["Timeline", "Phase Focus", "Engineering Deliverables", "Quality Delivery Gate"]
    t3_rows = [
        ["Week 1", "Foundations & Setup", "Literature review, taxonomy definition, Git repo and PyTorch environment setup.", "Workspace Ready"],
        ["Week 2", "Data Ingestion & Splits", "Patient-wise split (Zero Leakage), 512×512 letterbox, multi-task sampler 60:25:15.", "Gate 1: Data Integrity"],
        ["Week 3", "Multi-Task Baseline", "MultiTaskChestXrayNet architecture, masked backpropagation, baseline checkpoint.", "Gate 2: Baseline Model"],
        ["Week 4", "Loss Optimization", "Asymmetric Loss (ASL) and dynamic Focal Loss, Youden's J threshold calibration.", "Gate 3: Loss Stability"],
        ["Week 5", "XAI & Shortcut Audit", "Grad-CAM++, VinDr & RSNA Box-IoU benchmarking, in-lung activation audit (>= 80%).", "Gate 4: WSOL Grounding"],
        ["Week 6", "Full-Stack PACS Serving", "FastAPI asynchronous microservice (<= 1.8s) and Next.js 14 PACS viewer integration.", "PACS Integration"],
        ["Week 7", "Clinical Fail-Safe Layer", "Helmholtz Free Energy OOD lockout implementation and structured ICD-10 reporting.", "Gate 5: Clinical Safety"],
        ["Week 8", "Regression Testing", "138 automated unit tests PASS (verify.ps1), container packaging, latency optimization.", "Regression Closure"],
        ["Week 9", "Final Thesis & Defense", "Comprehensive thesis report, 40-slide defense presentation deck, video walkthrough.", "Gate 6: Final Defense"],
    ]
    pdf.draw_booktabs_table(t3_headers, t3_rows, [22, 38, 75, 35])

    # ------------------ SUMMARY & SIGN-OFF ------------------
    pdf.ln(3)
    pdf.section_title("II. PROPOSAL SUMMARY & SIGN-OFF")
    pdf.paragraph(
        "The LungRay platform addresses an urgent clinical challenge by combining state-of-the-art multi-task deep learning "
        "with trustworthy explainability and out-of-distribution clinical safety guardrails. Group 11 is committed to executing "
        "this project under rigorous scientific integrity, delivering a production-grade medical AI platform ready for clinical decision support."
    )
    pdf.ln(4)

    # Signatures
    pdf.set_font("TimesNR", "B", 9.2)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(85, 5, "Submitted by Project Team (Group 11):", border=0, align="L")
    pdf.cell(85, 5, "Academic Supervisor Approval:", border=0, align="L")
    pdf.ln(14)

    pdf.set_font("TimesNR", "", 9.2)
    pdf.cell(85, 4.5, "Tan Phat & Manh", border=0, align="L")
    pdf.cell(85, 4.5, "[Academic Supervisor Name]", border=0, align="L")
    pdf.ln(4.0)
    pdf.cell(85, 4.5, "Date: November 9, 2026", border=0, align="L")
    pdf.cell(85, 4.5, "Date: ________________________", border=0, align="L")

    # Output files
    pdf_out_dir = WORKSPACE_ROOT / "reports" / "output" / "pdf"
    pdf_out_dir.mkdir(parents=True, exist_ok=True)
    target_pdf = pdf_out_dir / "LungRay_Report_1_Project_Proposal.pdf"
    root_pdf = WORKSPACE_ROOT / "reports" / "LungRay_Report_1_Project_Proposal.pdf"

    pdf.output(str(target_pdf))
    import shutil
    shutil.copyfile(target_pdf, root_pdf)

    size_kb = target_pdf.stat().st_size / 1024
    print(f"[OK] Report #1 PDF successfully generated at: {target_pdf} ({size_kb:.1f} KB)")
    print(f"[OK] Mirrored to root reports: {root_pdf}")

if __name__ == "__main__":
    build_proposal_pdf()
