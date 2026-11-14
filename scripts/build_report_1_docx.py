#!/usr/bin/env python3
"""
scripts/build_report_1_docx.py - Build Publication-Grade Word Document (.docx) for Report #1 (Project Proposal)
Adheres strictly to Rule 9 and DSP391 Capstone Report standards:
- Typography: Times New Roman, 11pt body, 1.15 line spacing, justified.
- Headings: Styled Heading 1, Heading 2, Heading 3.
- Tables: Authentic Booktabs style (thick top/bottom borders, header border, zero vertical lines).
- Output: reports/output/LungRay_Report_1_Project_Proposal.docx and reports/LungRay_Report_1_Project_Proposal.docx
"""
import os
import sys
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

def set_cell_border(cell, **kwargs):
    """Sets individual cell borders."""
    tcPr = cell._element.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key, val in edge_data.items():
                element.set(qn(f'w:{key}'), str(val))

def apply_booktabs_table_style(table, col_widths=None):
    """Applies authentic academic Booktabs styling."""
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    num_rows = len(table.rows)
    for i, row in enumerate(table.rows):
        trPr = row._element.get_or_add_trPr()
        trPr.append(parse_xml(r'<w:cantSplit {}/>'.format(nsdecls('w'))))
        
        if i == 0:
            trPr.append(parse_xml(r'<w:tblHeader {}/>'.format(nsdecls('w'))))

        for j, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if col_widths and j < len(col_widths):
                cell.width = Inches(col_widths[j])

            border_kwargs = {}
            if i == 0:
                border_kwargs['top'] = {"sz": 12, "val": "single", "color": "000000"}
                border_kwargs['bottom'] = {"sz": 8, "val": "single", "color": "000000"}
                shading = parse_xml(r'<w:shd {} w:fill="F4F4F6"/>'.format(nsdecls('w')))
                cell._tc.get_or_add_tcPr().append(shading)
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in p.runs:
                        run.font.bold = True
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(9.5)
            elif i == num_rows - 1:
                border_kwargs['bottom'] = {"sz": 12, "val": "single", "color": "000000"}
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(9.0)
            else:
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(9.0)
            
            border_kwargs['left'] = {"val": "none"}
            border_kwargs['right'] = {"val": "none"}
            set_cell_border(cell, **border_kwargs)

def add_heading_styled(doc, text, level):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(14 if level == 1 else (10 if level == 2 else 6))
    p.paragraph_format.space_after = Pt(4)
    for r in p.runs:
        r.font.name = "Times New Roman"
        r.font.color.rgb = RGBColor(0, 0, 0)
        if level == 1:
            r.font.size = Pt(15)
            r.font.bold = True
        elif level == 2:
            r.font.size = Pt(12.5)
            r.font.bold = True
        else:
            r.font.size = Pt(11)
            r.font.bold = True
            r.font.italic = True
    return p

def add_body_p(doc, text, bold_prefix=None, space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(11)
        r_pre.font.bold = True
    
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    return p

def add_bullet_p(doc, bold_prefix, text, space_after=3):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    if bold_prefix:
        r_pre = p.add_run(bold_prefix + ": ")
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(11)
        r_pre.font.bold = True
    
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    return p

def add_caption(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(9.5)
    r.font.italic = True
    return p

def build_docx_report_1():
    doc = Document()
    
    # Page setup: Standard A4, 1-inch margins
    sections = doc.sections
    for section in sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # ------------------ TITLE & COVER BANNER ------------------
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    p_title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("LUNGRAY: MULTI-TASK CLINICAL CADX AND TRUSTWORTHY WSOL GROUNDING PLATFORM")
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(16)
    r_title.font.bold = True

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(4)
    p_sub.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("CAPSTONE PROJECT PROPOSAL (REPORT #1) — COURSE CODE: DSP391")
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(11.5)
    r_sub.font.bold = True

    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(0)
    p_meta.paragraph_format.space_after = Pt(12)
    p_meta.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_meta = p_meta.add_run(
        "Specialization: Artificial Intelligence & Data Science | Department of Computer Science\n"
        "FPT University, Ho Chi Minh City Campus — November 2026"
    )
    r_meta.font.name = "Times New Roman"
    r_meta.font.size = Pt(10)
    r_meta.font.italic = True
    r_meta.font.color.rgb = RGBColor(80, 80, 80)

    # Metadata Summary Box
    p_box = doc.add_paragraph()
    p_box.paragraph_format.space_after = Pt(8)
    p_box.paragraph_format.line_spacing = 1.15
    
    r = p_box.add_run("Project Team (Group 11): "); r.bold = True; r.font.name = "Times New Roman"
    r = p_box.add_run("Tan Phat (Lead AI Architect & Systems Engineer) & Manh (AI Research & Data Operations Engineer)\n"); r.font.name = "Times New Roman"
    r = p_box.add_run("Academic Supervisor: "); r.bold = True; r.font.name = "Times New Roman"
    r = p_box.add_run("[Supervisor Name] | Faculty of Computer Science & Artificial Intelligence\n"); r.font.name = "Times New Roman"
    r = p_box.add_run("Technical Repository: "); r.bold = True; r.font.name = "Times New Roman"
    r = p_box.add_run("https://github.com/philipsgn/LungRay.git | Schedule: 9-Week Accelerated Capstone Cycle"); r.font.name = "Times New Roman"

    # ------------------ CHAPTER I: PROJECT INTRODUCTION ------------------
    add_heading_styled(doc, "I. PROJECT INTRODUCTION", level=1)

    # 1. Overview
    add_heading_styled(doc, "1. Overview", level=2)
    add_heading_styled(doc, "1.1 Project Information", level=3)
    add_body_p(
        doc,
        "The operational metadata, team governance, and institutional stakeholders for the LungRay capstone initiative "
        "are systematically documented in Table 1.1."
    )

    add_caption(doc, "Table 1.1: Project Information and Organizational Metadata.")
    t1_data = [
        ["Attribute", "Detailed Specification"],
        ["Project Name", "LungRay: Multi-Task Clinical CADx and Trustworthy WSOL Grounding Platform"],
        ["Project Code", "DSP391 (System Code: DSP391-LUNGRAY-CADX-2026) | Group: Group 11"],
        ["Team Members", "Tan Phat (Lead AI Architect & Systems Engineer)\nManh (AI Research & Data Operations Engineer)"],
        ["Academic Supervisor", "[Supervisor Name] — Faculty of Computer Science & Artificial Intelligence, FPT University"],
        ["Key Stakeholders", "Radiologists (Triaging & Second Reader), Emergency Clinicians, Capstone Academic Committee"],
        ["Core Architecture", "Multi-Task 3-Head CNN (Shared DenseNet-121 Encoder, 512×512 Input Resolution)"],
        ["Diagnostic Scope", "16 Cardiopulmonary Conditions (14 NIH Thoracic Pathologies + Tuberculosis + COVID-19)"],
        ["Safety Systems", "Helmholtz Free Energy Out-of-Distribution Lockout (Tau_E = 9.0421) & Multi-Scale Grad-CAM++ IoU"],
    ]
    t1 = doc.add_table(rows=len(t1_data), cols=2)
    for r_idx, row in enumerate(t1_data):
        for c_idx, val in enumerate(row):
            t1.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    apply_booktabs_table_style(t1, col_widths=[1.8, 4.47])

    add_heading_styled(doc, "1.2 Project Overview", level=3)
    add_body_p(
        doc,
        "Chest radiography (Chest X-ray, CXR) constitutes the single most frequently performed projectional imaging examination "
        "in modern clinical medicine, representing over 40% of all diagnostic imaging workloads worldwide. Radiologists routinely inspect "
        "projectional radiographs to detect pulmonary infections, thoracic masses, cardiac enlargement, pleural effusion, and chronic "
        "parenchymal disorders. However, healthcare institutions globally confront a dual crisis: exponential growth in scan volumes "
        "contrasted against an acute shortage of certified radiologists. This disparity induces substantial cognitive fatigue, "
        "prolonged diagnostic turnaround times (24 to 72 hours in resource-constrained environments), and diagnostic discrepancy rates "
        "between 10% and 30% in high-pressure emergency triaging."
    )
    add_body_p(
        doc,
        "The LungRay initiative establishes an enterprise-grade Computer-Aided Diagnosis (CADx) and Clinical Decision Support (CDS) "
        "platform specifically designed to overcome these institutional bottlenecks. Moving beyond conventional, siloed single-disease models, "
        "LungRay formulates a unified Multi-Task 3-Head Convolutional Neural Network driven by a shared DenseNet-121 visual encoder. "
        "The platform executes simultaneous, holistic screening across sixteen cardiopulmonary pathologies while enforcing Weakly-Supervised "
        "Object Localization (WSOL) via Multi-Scale Grad-CAM++ to render decisions visually and mathematically interpretable."
    )

    # 2. Project Background
    add_heading_styled(doc, "2. Project Background", level=2)
    add_body_p(
        doc,
        "Projectional chest radiography provides a high-resolution, low-cost anatomical survey of thoracic structures, including the "
        "pulmonary parenchyma, pleural spaces, mediastinum, cardiac silhouette, and bony thorax. Interpreting planar CXRs represents an intricate "
        "perceptual and cognitive challenge. Cardiopulmonary pathologies manifest as subtle gradations in radiopacity, overlapping soft-tissue shadows, "
        "and ambiguous anatomical margins. For instance, early-stage solitary pulmonary nodules or retrocardiac consolidations frequently obscure "
        "within normal vascular markings or diaphragmatic contours."
    )
    add_body_p(
        doc,
        "In low- and middle-income healthcare systems, regional referral clinics frequently operate without dedicated on-site thoracic radiologists. "
        "General practitioners must review complex radiographs under extreme time constraints. In infectious disease epidemics—such as active "
        "pulmonary tuberculosis surges or viral pneumonia outbreaks—delayed identification of positive cases accelerates nosocomial transmission "
        "and compromises patient prognoses."
    )
    add_body_p(
        doc,
        "While deep learning has demonstrated expert-level accuracy on curated datasets, clinical translation has been severely obstructed by three "
        "systemic deficiencies in prior medical AI systems:"
    )
    add_bullet_p(
        doc,
        "Task Siloization and Memory Redundancy",
        "The vast majority of published models address only a solitary diagnostic target (e.g., exclusively detecting COVID-19 or solely binary pneumonia). "
        "Deploying multiple disjoint single-task models requires loading dozens of discrete neural networks into memory, resulting in unsustainable GPU VRAM overhead and fragmented inference pipelines."
    )
    add_bullet_p(
        doc,
        "Extreme Positive-Negative Class Imbalance",
        "Within multi-label thoracic radiography cohorts (such as the NIH ChestX-ray14 dataset), positive prevalence for critical conditions like Hernia (0.2%) "
        "or Pneumothorax (4.7%) is heavily suppressed by dominant negative instances (over 95% to 99% negative per pathology). Traditional Binary Cross-Entropy loss functions collapse toward the majority negative class, failing to optimize discriminative boundaries for critical minority findings."
    )
    add_bullet_p(
        doc,
        "Confounder Memorization (Shortcut Learning)",
        "Deep convolutional networks routinely learn non-physiological shortcuts (such as hospital-specific metal orientation markers 'R'/'L', radiopaque wires, and detector border artifacts) rather than true pathology, resulting in failure when tested across external hospitals."
    )

    # 3. Project Objectives
    add_heading_styled(doc, "3. Project Objectives", level=2)
    add_body_p(
        doc,
        "The overarching engineering objective of the LungRay platform is to develop, validate, and deploy a trustworthy multi-task deep learning system "
        "that delivers rapid, calibrated, and interpretable chest radiograph triaging without violating clinical safety constraints. The concrete measurable objectives comprise:"
    )
    add_bullet_p(doc, "Unified Multi-Task Architecture", "Construct MultiTaskChestXrayNet operating at 512×512 resolution, isolating gradients across 3 heads via parameter-free LayerNorm feature projection.")
    add_bullet_p(doc, "Zero Patient-Level Data Leakage", "Enforce strict patient-wise partitioning ensuring zero overlapping Patient_ID instances across train/val/test splits (70/10/20 on NIH ChestX-ray14), preventing artificial performance inflation.")
    add_bullet_p(doc, "Multi-Task Batch Equilibrium", "Formulate WeightedMultiTaskBatchSampler maintaining an exact ratio of 60% NIH : 25% COVIDx : 15% TB per mini-batch, eliminating gradient starvation across heterogeneous tasks.")
    add_bullet_p(doc, "Imbalance Mitigation via Asymmetric Loss", "Implement Asymmetric Loss (ASL) with probability margin m = 0.05 to elevate minority-class multi-label ROC-AUC above 0.82 on Head A without suppressing minority classes.")
    add_bullet_p(doc, "Trustworthy WSOL Localization", "Deploy Multi-Scale Grad-CAM++ achieving Mean Box-IoU >= 0.35 against expert radiologist bounding boxes (VinDr-CXR and RSNA) without box supervision during training.")
    add_bullet_p(doc, "Shortcut Learning Audit & Defeat", "Enforce automated dilated lung masking, ensuring that >= 80% of gradient activation energy resides within anatomical lung fields on COVID-19 positive radiographs.")
    add_bullet_p(doc, "Clinical Fail-Safe Layer", "Deploy Helmholtz Free Energy Out-of-Distribution screening to identify and reject corrupted or non-CXR inputs prior to classification.")
    add_bullet_p(doc, "Sub-Two-Second PACS Serving", "Containerize the platform into an asynchronous FastAPI backend delivering inference within <= 1.8 seconds, paired with a Next.js 14 Medical PACS Darkroom Viewer (#070B12).")

    # 4. Problem Statement
    add_heading_styled(doc, "4. Problem Statement", level=2)
    add_body_p(
        doc,
        "Formally, let an input frontal chest radiograph be formalized as an image tensor X in R^(3 × 512 × 512). "
        "The multi-task CADx system must map X to a compound diagnostic prediction vector Y_hat = {y_hat_A, y_hat_B, y_hat_C} "
        "parameterized by a shared convolutional encoder f_theta(X):"
    )
    add_body_p(
        doc,
        "    • y_hat_A = sigma(g_phi_A(f_theta(X))) in [0, 1]^14   (Bernoulli probabilities for 14 NIH thoracic findings)\n"
        "    • y_hat_B = sigma(g_phi_B(f_theta(X))) in [0, 1]        (Scalar probability of active pulmonary tuberculosis)\n"
        "    • y_hat_C = Softmax(g_phi_C(f_theta(X))) in [0, 1]^3     (Probabilities for COVID-19 differential triage)"
    )
    add_body_p(
        doc,
        "The fundamental machine learning challenges in solving this problem simultaneously include resolving disjoint dataset label spaces, "
        "overcoming the 98.6% negative label ratio in multi-label loss gradients, extracting multi-focal lesion bounding boxes without spatial supervision, "
        "and preserving real-time clinical latency."
    )

    # 5. Significance of the Project
    add_heading_styled(doc, "5. Significance of the Project", level=2)
    add_bullet_p(
        doc,
        "Clinical Impact & Patient Outcomes",
        "Functions as an automated intelligent second-reader. In emergency departments, it automatically triages incoming CXRs, flagging life-threatening conditions (such as Tension Pneumothorax, Massive Pleural Effusion, or Severe Bilateral Consolidation) for immediate, prioritized radiologist review within two minutes of image capture."
    )
    add_bullet_p(
        doc,
        "Academic & Methodological Novelty",
        "The project provides empirical proof that a single shared DenseNet-121 encoder can achieve discriminative performance matching or exceeding three independent single-task networks while slashing GPU memory requirements by 66%. Furthermore, our quantitative Bounding Box IoU benchmarking establishes an objective standard over purely qualitative heatmap inspection."
    )
    add_bullet_p(
        doc,
        "Economic & Healthcare Resource Optimization",
        "By containerizing the entire inference pipeline into a lightweight Docker microservice with dynamic CPU/GPU fallback, LungRay can be deployed on low-cost edge servers in rural provincial hospitals without requiring continuous internet connectivity or multi-thousand-dollar GPU clusters."
    )

    # 6. Project Scope & Limitations
    add_heading_styled(doc, "6. Project Scope & Limitations", level=2)
    add_body_p(doc, "To establish rigorous clinical safety and prevent inappropriate system usage, explicit boundaries are defined:")
    add_bullet_p(doc, "In-Scope Capabilities", "Adult frontal projection chest radiographs acquired in Posteroanterior (PA) or Anteroposterior (AP) views; automated scoring across 16 specified thoracic conditions; interactive Grad-CAM++ overlays; Free Energy OOD safety screening; responsive Next.js darkroom viewer.")
    add_bullet_p(doc, "Pediatric Radiographs Excluded", "Anatomical proportions, ossification centers, and normal cardiothoracic ratios in neonates and young children differ significantly from adults; pediatric cohorts are strictly excluded from the operational scope.")
    add_bullet_p(doc, "Lateral Projection CXRs Excluded", "Only frontal projection radiographs are supported; lateral chest views are beyond current processing capabilities.")
    add_bullet_p(doc, "Non-Autonomous Classification", "LungRay is explicitly designed as an assistive second-reader (Class IIa Medical Software). It does not issue autonomous definitive clinical diagnoses or prescribe therapeutic regimens. All outputs require validation by a licensed medical practitioner.")

    # 7. Preliminary Research & Proposed Technical Approach
    add_heading_styled(doc, "7. Preliminary Research & Proposed Technical Approach", level=2)
    add_body_p(
        doc,
        "To ensure clinical generalization and eliminate institutional bias, the platform curates and standardizes six internationally recognized open-access medical imaging cohorts, encompassing over 142,000 chest radiographs (Table 1.2)."
    )

    add_caption(doc, "Table 1.2: Standardized Clinical Radiography Datasets in LungRay Platform.")
    t2_data = [
        ["Dataset Identifier", "Clinical Scope", "Cohort Size", "Primary Function in Project"],
        ["NIH ChestX-ray14", "14 Thoracic Pathologies", "112,120 CXRs", "Head A Multi-Label Training & Testing"],
        ["TB Chest Radiography", "Pulmonary Tuberculosis", "7,000 CXRs", "Head B Tuberculosis Screening"],
        ["COVIDx CXR-4", "COVID-19 / Pneumonia / Normal", "16,400+ CXRs", "Head C COVID-19 Differential Triage"],
        ["VinDr-CXR", "Vietnamese Thoracic Cohort", "3,000 CXRs", "Quantitative WSOL IoU External Benchmark"],
        ["RSNA Pneumonia", "Pneumonia Consolidations", "6,000+ CXRs", "Quantitative WSOL IoU External Benchmark"],
        ["Stanford CheXpert", "External Multi-Label Cohort", "1,000 CXRs", "Out-of-Distribution Generalization Audit"],
    ]
    t2 = doc.add_table(rows=len(t2_data), cols=4)
    for r_idx, row in enumerate(t2_data):
        for c_idx, val in enumerate(row):
            t2.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    apply_booktabs_table_style(t2, col_widths=[1.5, 1.8, 1.1, 1.87])

    # 8. Project Execution Plan & Milestones
    add_heading_styled(doc, "8. Project Execution Plan & Milestones", level=2)
    add_body_p(
        doc,
        "The project is structured across an accelerated 9-week execution lifecycle, organized into agile sprint deliverables and verified through six formal Quality Delivery Gates (Table 1.3)."
    )

    add_caption(doc, "Table 1.3: Nine-Week Project Execution Roadmap and Quality Delivery Gates.")
    t3_data = [
        ["Timeline", "Phase Focus", "Engineering Deliverables", "Quality Delivery Gate"],
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
    t3 = doc.add_table(rows=len(t3_data), cols=4)
    for r_idx, row in enumerate(t3_data):
        for c_idx, val in enumerate(row):
            t3.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    apply_booktabs_table_style(t3, col_widths=[0.8, 1.4, 2.67, 1.4])

    # ------------------ SUMMARY & SIGN-OFF ------------------
    add_heading_styled(doc, "II. PROPOSAL SUMMARY & SIGN-OFF", level=1)
    add_body_p(
        doc,
        "The LungRay platform addresses an urgent, high-impact clinical challenge by coupling state-of-the-art multi-task deep learning "
        "with trustworthy explainability and out-of-distribution clinical safety guardrails. Group 11 is committed to executing this project under "
        "rigorous scientific integrity, delivering a production-grade medical artificial intelligence platform ready for clinical decision support."
    )

    # Signature Block
    p_sig = doc.add_paragraph()
    p_sig.paragraph_format.space_before = Pt(14)
    p_sig.paragraph_format.space_after = Pt(2)
    
    t_sig = doc.add_table(rows=4, cols=2)
    t_sig.rows[0].cells[0].paragraphs[0].text = "Submitted by Project Team (Group 11):"
    t_sig.rows[0].cells[0].paragraphs[0].runs[0].bold = True
    t_sig.rows[0].cells[1].paragraphs[0].text = "Academic Supervisor Approval:"
    t_sig.rows[0].cells[1].paragraphs[0].runs[0].bold = True
    
    t_sig.rows[1].cells[0].paragraphs[0].text = "\n\n"
    t_sig.rows[1].cells[1].paragraphs[0].text = "\n\n"
    
    t_sig.rows[2].cells[0].paragraphs[0].text = "Tan Phat & Manh"
    t_sig.rows[2].cells[1].paragraphs[0].text = "[Academic Supervisor Name]"
    
    t_sig.rows[3].cells[0].paragraphs[0].text = "Date: November 9, 2026"
    t_sig.rows[3].cells[1].paragraphs[0].text = "Date: ________________________"
    
    for row in t_sig.rows:
        for cell in row.cells:
            cell.paragraphs[0].runs[0].font.name = "Times New Roman"
            cell.paragraphs[0].runs[0].font.size = Pt(10)
            set_cell_border(cell, top={"val": "none"}, bottom={"val": "none"}, left={"val": "none"}, right={"val": "none"})

    # Output file paths
    out_dir = WORKSPACE_ROOT / "reports" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    target_docx = out_dir / "LungRay_Report_1_Project_Proposal.docx"
    root_docx = WORKSPACE_ROOT / "reports" / "LungRay_Report_1_Project_Proposal.docx"

    doc.save(str(target_docx))
    import shutil
    shutil.copyfile(target_docx, root_docx)

    size_kb = target_docx.stat().st_size / 1024
    print(f"[OK] Report #1 DOCX successfully created at: {target_docx} ({size_kb:.1f} KB)")
    print(f"[OK] Mirrored to root reports: {root_docx}")

if __name__ == "__main__":
    build_docx_report_1()
