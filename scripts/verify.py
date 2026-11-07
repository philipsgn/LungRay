#!/usr/bin/env python3
"""
scripts/verify.py - Comprehensive Verification Runner for LungRay Platform.
Usage: python scripts/verify.py or powershell -File scripts/verify.ps1
"""
import sys
import subprocess
import shutil

# Reconfigure stdout/stderr to utf-8 if possible
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_step(step_name: str, cmd: list) -> bool:
    print(f"\n[+] Running: {step_name}...")
    try:
        res = subprocess.run(cmd, check=False)
        if res.returncode != 0:
            print(f"[FAIL] {step_name} (Exit code: {res.returncode})")
            return False
        print(f"[PASS] {step_name}")
        return True
    except Exception as e:
        print(f"[ERROR] {step_name} - {e}")
        return False

def check_model_and_docs_integrity() -> bool:
    """
    Step 4: Validates the 7 Core Synchronization Documents, verifies 0 raw LaTeX $
    in publication markdown files, checks configuration validity, and confirms figure assets.
    """
    from pathlib import Path
    import json

    workspace = Path(__file__).resolve().parent.parent
    print("\n[+] Running: Model & Documentation Integrity Check (Rule 10)...")
    
    # 1. Verify 7 Core Synchronization Documents
    core_docs = [
        "TECH_ARCHITECTURE.md",
        "PRD.md",
        "PHASES.md",
        "reports/DSP391_Full_Thesis_Report.md",
        "reports/docs_report.md",
        "reports/LANDING_PAGE_REPORT.html",
        "docs/DEMO_PRESENTATION_GUIDE.md",
    ]
    for rel_path in core_docs:
        p = workspace / rel_path
        if not p.exists():
            print(f"  [FAIL] Missing mandatory sync document: {rel_path}")
            return False
        if p.stat().st_size == 0:
            print(f"  [FAIL] Mandatory sync document is empty: {rel_path}")
            return False
    print("  [PASS] All 7 Core Synchronization Documents exist and are non-empty.")

    # 2. Verify Zero Raw LaTeX Dollar Signs in Target Reports
    latex_docs = [
        "reports/DSP391_Full_Thesis_Report.md",
        "reports/docs_report.md",
    ]
    for rel_path in latex_docs:
        p = workspace / rel_path
        text = p.read_text(encoding="utf-8")
        if "$" in text:
            dollar_count = text.count("$")
            print(f"  [FAIL] Found {dollar_count} raw LaTeX '$' symbols in {rel_path} (Violates Word Copy-Paste Standard).")
            return False
    print("  [PASS] Zero raw LaTeX '$' symbols in publication thesis reports.")

    # 3. Verify Configuration Integrity
    cfg_path = workspace / "configs" / "optimal_thresholds.json"
    if not cfg_path.exists():
        print("  [FAIL] Missing configs/optimal_thresholds.json")
        return False
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for head in ["head_a_nih_14", "head_b_tb", "head_c_covid"]:
            if head not in cfg:
                print(f"  [FAIL] Missing '{head}' in configs/optimal_thresholds.json")
                return False
        print("  [PASS] Decision threshold configuration (optimal_thresholds.json) is valid.")
    except Exception as e:
        print(f"  [FAIL] Could not parse configs/optimal_thresholds.json: {e}")
        return False

    # 4. Verify Embedded Figure Assets Exist
    expected_figures = [
        "results/eda/01_nih_class_distribution.png",
        "results/eda/02_nih_cooccurrence_matrix.png",
        "results/eda/03_nih_patient_demographics.png",
        "results/eda/04_covid_class_and_source.png",
        "results/eda/05_tb_class_distribution.png",
        "results/eda/06_multi_task_sampler_ratio.png",
        "results/eda/07_real_cxr_samples_grid.png",
        "results/baseline/training_curves.png",
        "results/baseline/head_a_roc_curves.png",
        "results/baseline/head_b_tb_evaluation.png",
        "results/baseline/head_c_covid_evaluation.png",
        "results/figures/architecture_radar_comparison.png",
        "results/shortcut_audit_comparison.png",
        "results/shortcut_audit_summary.png",
        "results/wsol_finetune_curves.png",
    ]
    missing_figs = []
    for fig in expected_figures:
        if not (workspace / fig).exists():
            missing_figs.append(fig)
    if missing_figs:
        print(f"  [FAIL] Missing {len(missing_figs)} required figure assets: {missing_figs}")
        return False
    print(f"  [PASS] All {len(expected_figures)} empirical figure assets verified on disk.")

    print("[PASS] Model & Documentation Integrity Check")
    return True


def main():
    print("=" * 60)
    print(" [LungRay] AUTOMATED CODE VERIFICATION RUNNER")
    print("=" * 60)
    
    # 1. Compile & Syntax Check
    if not run_step("Compileall (Python Syntax Check)", [sys.executable, "-m", "compileall", "src", "tests", "-q"]):
        sys.exit(1)
        
    # 2. Linting (Ruff or Flake8 if available)
    if shutil.which("ruff"):
        if not run_step("Ruff Linting", ["ruff", "check", "src", "tests", "--select", "E9,F63,F7,F82"]):
            sys.exit(1)
    elif shutil.which("flake8"):
        if not run_step("Flake8 Linting", ["flake8", "src", "tests", "--select=E9,F63,F7,F82"]):
            sys.exit(1)
    else:
        print("\n[*] Notice: Ruff/Flake8 not installed in this environment; basic syntax validated by compileall.")

    # 3. Pytest Unit Tests
    if not run_step("Pytest Unit Tests", [sys.executable, "-m", "pytest", "tests", "-q", "--tb=short"]):
        sys.exit(1)

    # 4. Model & Documentation Integrity Check (Rule 10)
    if not check_model_and_docs_integrity():
        print("\n[FAIL] Model & Documentation Integrity Check failed. Please resolve discrepancies.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(">>> SUCCESS: ALL CHECKS PASSED - READY FOR GATEKEEPER REVIEW <<<")
    print("=" * 60)
    sys.exit(0)

if __name__ == "__main__":
    main()
