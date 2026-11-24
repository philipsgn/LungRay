# LungRay: Multi-Task CXR CADx & Weakly-Supervised Object Localization Platform

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![PyTorch 2.0+](https://img.shields.io/badge/pytorch-2.0%2B-ee4c2c.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Verification: 183 Tests PASS](https://img.shields.io/badge/verification-183%2F183%20PASS-emerald.svg)](scripts/verify.ps1)
[![Standards: MICCAI / IEEE](https://img.shields.io/badge/standards-MICCAI%20%2F%20IEEE-indigo.svg)](reports/DSP391_Full_Thesis_Report.md)

> **Enterprise-Grade Clinical Computer-Aided Diagnosis (CADx) & Weakly-Supervised Object Localization (WSOL) System for Chest Radiographs (CXR) with 5-Tier Safety Defense, Nature MI Shortcut Audit, and Zero-Hallucination Grounded Clinical RAG.**

---

> [!IMPORTANT]
> **CLINICAL DISCLAIMER & REGULATORY INTENT**  
> LungRay is designed as an investigative **Second-Reader Clinical Decision Support (CDS / CADx) Triaging Platform** intended for academic research and pre-clinical validation. It is **not** an autonomous diagnostic device and does not replace the licensed clinical judgment of board-certified radiologists. Out-of-Distribution (OOD) radiographs, corrupt DICOM headers, or extreme visual artifacts automatically trigger the **Fail-Safe OOD Lockout Gatekeeper**, safely withholding automated conclusions.

---

## 📑 Table of Contents
1. [Executive Summary & Core Highlights](#1-executive-summary--core-highlights)
2. [5-Tier Safety & Trustworthy AI Architecture](#2-5-tier-safety--trustworthy-ai-architecture)
3. [Multi-Task 3-Head Neural Architecture](#3-multi-task-3-head-neural-architecture)
4. [Quantitative Empirical Benchmarks](#4-quantitative-empirical-benchmarks)
5. [Clinical PACS Workstation & Interactive Demo](#5-clinical-pacs-workstation--interactive-demo)
6. [Grounded Clinical RAG Assistant](#6-grounded-clinical-rag-assistant)
7. [The 9 Inviolable Engineering Constraints](#7-the-9-inviolable-engineering-constraints)
8. [6 Benchmark Medical Datasets](#8-6-benchmark-medical-datasets)
9. [Quick Start & 1-Click Launch](#9-quick-start--1-click-launch)
10. [Automated Verification & CI Quality Gates](#10-automated-verification--ci-quality-gates)
11. [Repository Structure](#11-repository-structure)
12. [License & Ethical Compliance](#12-license--ethical-compliance)

---

## 1. Executive Summary & Core Highlights

LungRay systematically resolves four fundamental bottlenecks in deep learning for thoracic radiology:

1. **Task Fragmentation & GPU Footprint Inflation**: Replaces siloed single-disease models with a **Shared Multi-Task Backbone** (DenseNet-121 / ResNet-50 / AG-MTCNet) simultaneously diagnosing **14 common thoracic diseases** (NIH ChestX-ray14), **Tuberculosis screening** (TB Portal), and **COVID-19 triaging** (COVIDx CXR-4) within a single 6.97M parameter forward pass.
2. **Shortcut Learning Elimination (Nature Machine Intelligence 2021)**: Overcomes severe confounding from hospital watermarks, text annotations (R/L markers), and diaphragm borders via **Clinical Pulmonary Grounding** and **Dense-UNet Anatomical Gating**, boosting in-lung lesion activation energy from 38.49% to **94.92%** ($p = 1.15 \times 10^{-26}$).
3. **Quantified Weakly-Supervised Object Localization (WSOL)**: Binarizes continuous Grad-CAM activation heatmaps with adaptive Youden thresholds, validating localization against expert radiologist bounding boxes from **VinDr-CXR** (Box-IoU 0.6049, 74.2% hit rate) and **RSNA Pneumonia** (Box-IoU 0.7631, 90.0% hit rate) without requiring any bounding boxes during training.
4. **5-Tier Clinical Safety Defense**: Complete defense-in-depth including Helmholtz Free Energy OOD Lockout ($S_E \ge 9.0421$, AUROC 1.0000), Smart Report Guardrails, and an offline, zero-hallucination Clinical RAG Assistant powered by WHO ICD-10, Fleischner Society 2024 terminology, and WHO guidelines.

---

## 2. 5-Tier Safety & Trustworthy AI Architecture

```
                          [ Incoming Chest X-ray (CXR) ]
                                        │
┌───────────────────────────────────────▼────────────────────────────────────────┐
│ TIER 1: Dense-UNet Anatomical Gate & Dilated Soft-Masking                      │
│ - Dense-UNet Segmentor: Val Dice 0.9630, IoU 0.9300 (Dubey et al. BMC 2026)   │
│ - Dilated Soft-Masking: 6% dilation, 10% attenuation                           │
│ - White-Out Fail-Safe: Automatic bypass if detected lung area < 5%             │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼────────────────────────────────────────┐
│ TIER 2: Shortcut Learning Audit & Clinical Pulmonary Grounding                 │
│ - Real-time Grad-CAM Energy Audit: In-Lung Activation Ratio >= 80% Threshold   │
│ - Eliminates peripheral tokens, R/L lead markers, and rib margin shortcuts     │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼────────────────────────────────────────┐
│ TIER 3: OOD Helmholtz Free Energy & Shannon Entropy Fail-Safe Lockout          │
│ - Energy Score: S_E = -T * logsumexp(logits / T) >= 9.0421                     │
│ - Shannon Entropy: H <= 0.6275 nats (Uncertainty Lockout)                      │
│ - AUROC 1.0000 on corrupted, inverted, or non-thoracic inputs                  │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼────────────────────────────────────────┐
│ TIER 4: Smart Clinical Report Guardrail                                        │
│ - Automatically downgrades false-positive suspect flags if in-lung ratio < 80% │
│ - Requires Head A parenchymal confirmation before raising secondary alerts     │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼────────────────────────────────────────┐
│ TIER 5: Deterministic Grounded Clinical RAG Assistant                          │
│ - Strictly offline, zero-LLM, zero-hallucination structured knowledge cards    │
│ - WHO ICD-10 coding notes, Fleischner Society (2024), WHO TB / COVID protocols │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Multi-Task 3-Head Neural Architecture

```
                          [ Input CXR: 3 x 512 x 512 ]
                                       │
                      ┌────────────────┴────────────────┐
                      │    Shared Multi-Task Encoder    │
                      │    (DenseNet-121 / ResNet-50)   │
                      └────────────────┬────────────────┘
                                       │ Feature Maps: 1024 x 16 x 16
                                       ▼
                          [ Global Average Pooling ]
                                       │
                         [ Parameter-Free LayerNorm ] (1024-d)
                                       │
                         [ Dropout Regularization: 0.2 ]
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 ▼                     ▼                     ▼
       ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
       │   Head A: NIH-14  │ │    Head B: TB     │ │   Head C: COVID   │
       │ Linear(1024, 14)  │ │  Linear(1024, 1)  │ │  Linear(1024, 1)  │
       │ Asymmetric Loss   │ │ BCEWithLogitsLoss │ │ BCEWithLogitsLoss │
       │ WHO ICD-10 Coded  │ │ ICD-10: A15.0/A16 │ │ ICD-10: U07.1     │
       │ Multi-Label Class │ │ Binary Screening  │ │ 3-Class Triage    │
       └─────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘
                 └─────────────────────┼─────────────────────┘
                                       ▼
                       [ Masked Multi-Task Loss Engine ]
             L_total = λ_A * M_A * L_A + λ_B * M_B * L_B + λ_C * M_C * L_C
```

- **Masked Backpropagation**: Strictly isolates gradients so mini-batches drawn from NIH-14 do not corrupt weights in Head B or Head C, completely preventing negative transfer.
- **Asymmetric Focal Loss (ASL)**: Overcomes severe positive class scarcity on Head A (95%+ negative samples) via asymmetric margin shifts ($\gamma_- = 4.0, \gamma_+ = 1.0$).
- **Weighted Batch Sampler**: Dynamically draws 60% NIH : 25% COVID : 15% TB samples per mini-batch, guaranteeing zero task starvation across heterogeneous datasets.

---

## 4. Quantitative Empirical Benchmarks

### 4.1. Multi-Head Classification Performance

All metrics evaluated under strict **Zero Patient Leakage (Patient-ID split)** on held-out test splits:

| Model Architecture | Head A (NIH-14) Macro AUROC | Head B (TB) AUROC | Head C (COVID) AUROC | Mean Multi-Task AUROC | Inference Latency (GPU / CPU) |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Standard CADx (DenseNet-121)** | **0.7858 Val / 0.7508 Test** | **0.9966 Val / 1.0000 Test** | **0.9787 Val / 0.7692 Test** | **0.8400** | 42 ms / 380 ms |
| **ResNet-50 Specialist** | 0.7412 Val / 0.7180 Test | 0.9980 Val / 1.0000 Test | 0.9891 Val / 0.7550 Test | 0.8243 | 48 ms / 410 ms |
| **WSOL Specialist** | 0.7290 Val / 0.7050 Test | 0.9684 Val / 0.9720 Test | 0.9410 Val / 0.7420 Test | 0.8063 | 45 ms / 395 ms |
| **AG-MTCNet 512×512 (Gate)** | 0.7479 Val / 0.6230 Test | 0.9986 Val / 0.9986 Test | 0.7479 Val / 0.6004 Test | 0.7407 | 62 ms / 490 ms |
| **Consensus Ensemble** | **0.7912 Val / 0.7620 Test** | **0.9990 Val / 1.0000 Test** | **0.9850 Val / 0.7810 Test** | **0.8477** | 135 ms / 1,180 ms |

### 4.2. Weakly-Supervised Object Localization (WSOL)

Evaluated against expert radiologist bounding box ground truths without any bounding box supervision during training:

| Benchmark Dataset | Ground Truth Source | Best Box-IoU | Localization Success Rate (IoU $\ge 0.10$) | Mean Precision |
|:---|:---|:---:|:---:|:---:|
| **RSNA Pneumonia Detection** | International Expert Consensus | **0.7631** | **90.0%** | 0.8420 |
| **VinDr-CXR Benchmark** | Board-Certified Vietnamese Radiologists | **0.6049** | **74.2%** | 0.7180 |

### 4.3. Shortcut Learning & Out-of-Distribution (OOD) Audit

| Evaluation Dimension | Baseline (Unmitigated) | LungRay Mitigation | Improvement / Statistical Significance |
|:---|:---:|:---:|:---:|
| **In-Lung Activation Energy Ratio** | 38.49% | **94.92%** | **+56.43%** ($p = 1.15 \times 10^{-26}$, Student's t-test) |
| **OOD Detection (Helmholtz $S_E$)** | 0.6210 AUROC | **1.0000 AUROC** | Perfect separation of inverted / non-chest inputs |
| **Dense-UNet Anatomical Segmentation** | N/A | **0.9630 Val Dice** | **0.9300 IoU** at 256px resolution |

---

## 5. Clinical PACS Workstation & Interactive Demo

LungRay provides a clinical-grade web PACS viewer conforming to DICOM standards:

- **Viewport Workstation**:
  - High-precision dual-view rendering (Original CXR, Grad-CAM Heatmap, Lesion Contour overlay).
  - Continuous Alpha-blend opacity slider ($0\% - 100\%$) with hardware-accelerated canvas blending.
  - One-click Anatomical Grounding filter toggle with live in-lung energy ratio monitoring.
  - Interactive pathology selector across all 16 supported conditions.
- **Diagnostic Findings & CDS Reporting**:
  - Quantitative prediction table with calibrated Youden thresholds ($\tau_c$).
  - Official ICD-10 clinical coding references for hospital billing and EHR integration.
  - Fail-Safe OOD Lockout status indicator and Smart Guardrail suspect banners.
  - One-click PDF / Print Export for clinical hand-off.

---

## 6. Grounded Clinical RAG Assistant

LungRay embeds a **deterministic, zero-hallucination Retrieval-Augmented Generation (RAG) assistant** for thoracic radiology:

- **Zero-LLM Architecture**: Operates 100% offline using structured rule-based knowledge cards, avoiding non-deterministic clinical hallucinations common to general LLMs.
- **Evidence-Based Knowledge Sources**:
  - **WHO ICD-10 International Classification of Diseases** (2019/2025).
  - **Fleischner Society Glossary of Terms for Thoracic Imaging** (*Radiology* 2024).
  - **WHO Consolidated Guidelines on Tuberculosis: Module 3 Diagnosis** (2025).
  - **WHO Guidelines on Chest Imaging in COVID-19** (2022).
- **Context-Aware Safety Filtering**: Automatically blocks medical commentary on OOD-rejected scans and annotates recommendations with in-lung energy audit ratios.

---

## 7. The 9 Inviolable Engineering Constraints

LungRay is engineered around **9 strict architectural and clinical constraints**:

1. **Multi-Task 3-Head Backbone**: Single shared encoder for Head A (14 NIH diseases), Head B (TB screening), and Head C (COVIDx).
2. **Zero Patient Leakage**: Strict `Patient_ID` partitioning on NIH-14 (70% train / 10% val / 20% test). Zero patient overlap between splits.
3. **Shortcut Learning Prevention**: Source-stratified partitioning on COVIDx by acquisition facility (`data_source`) and patient identifier.
4. **Bounding Box Separation**: Bounding boxes are **strictly reserved for WSOL evaluation** (VinDr-CXR, RSNA). Training is 100% weakly supervised.
5. **Dynamic Batch Balancing**: `WeightedMultiTaskBatchSampler` guarantees 60% NIH : 25% COVID : 15% TB representation per mini-batch.
6. **Mandatory Shortcut Auditing**: Head C activation heatmaps must achieve $\ge 80\%$ energy concentration within the lung field.
7. **Empirical Code Integrity**: Zero simulated charts or static mock images (`display(Image(...))`); all metrics computed from real inference pipelines.
8. **Lean Workspace Protocol**: Immediate automated cleanup of temporary runners, scratch scripts, and compile artifacts.
9. **Monochrome Academic Standards**: Complete IEEE/MICCAI compliance in reports and publications (Times New Roman, Booktabs 3-line tables, zero decorative emojis).

---

## 8. 6 Benchmark Medical Datasets

| Dataset | Scale | Role in Platform | Inviolable Constraint Applied |
|:---|:---:|:---|:---|
| **NIH ChestX-ray14** | 112,120 CXRs | Head A Training & Evaluation | Strict 70/10/20 `Patient_ID` non-overlapping split |
| **Tuberculosis (TB) Dataset** | 7,000 CXRs | Head B Screening | Fixed random seed; documentation of Shenzhen origin |
| **COVIDx CXR-4 Benchmark** | 16,400+ CXRs | Head C Triaging | Source-stratified by acquisition facility (`data_source`) |
| **VinDr-CXR (Test Only)** | 3,000 CXRs | WSOL Box-IoU Benchmark | Bounding boxes by board-certified Vietnamese radiologists |
| **RSNA Pneumonia (Test Only)**| 3,000 CXRs | WSOL Box-IoU Benchmark | International consensus pneumonia bounding boxes |
| **CheXpert-small-v1 (Test Only)**| 22,433 CXRs| OOD Generalization Audit | Hospital domain shift stress-testing |

---

## 9. Quick Start & 1-Click Launch

### Recommended: 1-Click PowerShell Launch
Automatically purges stale compile caches and starts both the FastAPI backend and Next.js frontend:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_local.ps1
```

- **Medical PACS Viewer**: [http://localhost:3000](http://localhost:3000)
- **Interactive 3D WSOL Atlas**: [http://localhost:3000/prototype/LungRay%20WSOL%20Atlas.html](http://localhost:3000/prototype/LungRay%20WSOL%20Atlas.html)
- **FastAPI OpenAPI Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **FastAPI Health Endpoint**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### Manual Component Startup

#### Backend Microservice (FastAPI + PyTorch)
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Workstation (Next.js 14 + TailwindCSS)
```powershell
cd app/frontend
npm install
npm run dev
```

---

## 10. Automated Verification & CI Quality Gates

The platform enforces 100% pass rates across **183 unit tests**, AST compile validation, Ruff linting, and Rule 10 documentation synchronization:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

### Verification Pipeline Checklist:
- `tests/test_api_backend.py`: FastAPI endpoints, multipart ingestion, 3-Pass TTA, and RAG retrieval.
- `tests/test_data_pipeline.py`: Zero Patient Leakage assertion, DICOM transforms, Weighted Sampler ratios.
- `tests/test_dense_unet.py` & `test_dense_unet_and_asl.py`: Dense-UNet Dice score, dilation soft-masking, ASL loss FP32 AMP safety.
- `tests/test_safety_guards.py`: 5-Tier safety defense, OOD Helmholtz lockout, Smart Guardrail suspect flags.
- `Rule 10 Model-to-Docs Sync`: Verification of 7 core synchronized documents and zero raw LaTeX `$` in Word-ready thesis reports.

---

## 11. Repository Structure

```
LungRay/
├── app/
│   ├── backend/               # FastAPI microservice (services.py, main.py, schemas.py)
│   └── frontend/              # Next.js 14 PACS viewer (components/, page.tsx, lib/)
├── configs/                   # Calibrated decision thresholds & model manifests
├── docs/                      # Clinical guides, presentation scripts & Kaggle manuals
├── notebooks/                 # Live empirical Jupyter notebooks (01 to 10)
├── prototype/                 # Interactive 3D WSOL Atlas (Three.js & Canvas)
├── reports/                   # Official thesis reports, HTML monographs & PDF publications
├── scripts/                   # Automated verify.ps1 runner & 1-click startup scripts
├── src/
│   ├── data/                  # Multi-Task Dataset, Sampler & Leakage-Free Splits
│   ├── explainability/        # Grad-CAM, Grad-CAM++, Adaptive Binarization, IoU Engine
│   ├── models/                # Multi-Task 3-Head Network, Dense-UNet, ASL Loss
│   └── safety/                # OOD Helmholtz Energy, Guardrails, Grounded Clinical RAG
└── tests/                     # 183 automated PyTest unit tests
```

---

## 12. License & Ethical Compliance

Distributed under the **MIT License**. All experimental workflows strictly comply with biomedical research ethics and Protected Health Information (PHI) de-identification standards (HIPAA / GDPR safe-harbor).
