"""
Unit Tests for LungRay Fail-Safe Safety Layer (Phase 8)
======================================================
Tests:
1. Sigmoid-adapted energy score computation (shapes, numerical stability, monotonic ordering).
2. Binary Shannon entropy computation (boundaries, maximum entropy at 0.5, minimum at 0/1).
3. SafetyPolicy decisions (accept criteria, reject criteria, config loading).
4. ClinicalReportGenerator (grounded generation, anatomical zone parsing, safety lockout).
"""
import numpy as np
import pytest
import torch

from src.safety.ood_scores import (
    compute_sigmoid_energy,
    compute_shannon_entropy,
    compute_max_sigmoid_confidence,
)
from src.safety.reject_policy import (
    SafetyDecision,
    SafetyPolicy,
    DEFAULT_ENERGY_THRESHOLD,
    DEFAULT_ENTROPY_THRESHOLD,
)
from src.safety.report_generator import (
    ClinicalReportGenerator,
    extract_anatomical_zone_from_heatmap,
)


def test_sigmoid_energy_shapes():
    """Verify energy returns correct shape for 1D, 2D tensors, and list inputs."""
    # 1D single-sample (14 classes)
    z1 = torch.randn(14)
    e1 = compute_sigmoid_energy(z1)
    assert isinstance(e1, torch.Tensor)
    assert e1.dim() == 0  # scalar
    assert e1.item() > 0.0

    # 2D batch (4 samples, 14 classes)
    z2 = torch.randn(4, 14)
    e2 = compute_sigmoid_energy(z2)
    assert e2.shape == (4,)
    assert (e2 > 0.0).all()

    # Python list
    e3 = compute_sigmoid_energy([1.0, 2.0, -1.0])
    assert e3.item() > 0.0


def test_sigmoid_energy_monotonicity():
    """Higher logits (ID-like activations) must strictly yield higher energy."""
    high_logits = torch.ones(14) * 3.0
    low_logits = torch.ones(14) * -3.0
    e_high = compute_sigmoid_energy(high_logits)
    e_low = compute_sigmoid_energy(low_logits)
    assert e_high.item() > e_low.item()


def test_shannon_entropy_boundaries():
    """Entropy must be maximized at p=0.5 and minimized at p near 0 or 1."""
    # Ambiguous predictions: all 0.5 -> max entropy = ln(2) ~= 0.6931
    ambiguous_probs = torch.ones(14) * 0.5
    h_max = compute_shannon_entropy(ambiguous_probs)
    assert pytest.approx(h_max.item(), abs=1e-3) == 0.6931

    # Highly confident predictions: all 0.01 or 0.99 -> low entropy
    confident_probs = torch.ones(14) * 0.01
    h_min = compute_shannon_entropy(confident_probs)
    assert h_min.item() < 0.1
    assert h_min.item() >= 0.0

    # 2D batch
    batch_probs = torch.rand(5, 14)
    h_batch = compute_shannon_entropy(batch_probs)
    assert h_batch.shape == (5,)
    assert (h_batch >= 0.0).all()


def test_max_sigmoid_confidence():
    """Confidence distance should be 0 at p=0.5 and 1 at p=0 or p=1."""
    p_neutral = torch.ones(14) * 0.5
    conf_neutral = compute_max_sigmoid_confidence(p_neutral)
    assert pytest.approx(conf_neutral.item(), abs=1e-4) == 0.0

    p_extreme = torch.zeros(14)
    p_extreme[0] = 1.0
    conf_extreme = compute_max_sigmoid_confidence(p_extreme)
    assert pytest.approx(conf_extreme.item(), abs=1e-4) == 1.0


def test_safety_policy_accept():
    """Standard ID conditions must produce ACCEPT."""
    policy = SafetyPolicy(energy_threshold=9.50, entropy_threshold=0.42)
    # High energy, low entropy -> ACCEPT
    decision = policy.evaluate(energy_score=15.0, entropy_score=0.15)
    assert decision.decision == "ACCEPT"
    assert decision.is_safe is True
    assert len(decision.rejection_reasons) == 0
    d_dict = decision.to_dict()
    assert d_dict["decision"] == "ACCEPT"


def test_safety_policy_reject_low_energy():
    """Low energy triggers REJECT with appropriate explanation."""
    policy = SafetyPolicy(energy_threshold=9.50, entropy_threshold=0.42)
    decision = policy.evaluate(energy_score=5.0, entropy_score=0.20)
    assert decision.decision == "REJECT"
    assert decision.is_safe is False
    assert any("năng lượng thấp" in r for r in decision.rejection_reasons)


def test_safety_policy_reject_high_entropy():
    """High entropy triggers REJECT with appropriate explanation."""
    policy = SafetyPolicy(energy_threshold=9.50, entropy_threshold=0.42)
    decision = policy.evaluate(energy_score=12.0, entropy_score=0.55)
    assert decision.decision == "REJECT"
    assert decision.is_safe is False
    assert any("hỗn loạn" in r for r in decision.rejection_reasons)


def test_safety_policy_reject_hyper_energy():
    """Hyper-activated energy (e.g. S_E = 33.97 from pediatric scan) triggers REJECT."""
    policy = SafetyPolicy(energy_threshold=9.04, energy_upper_threshold=22.0, entropy_threshold=0.62)
    decision = policy.evaluate(energy_score=33.97, entropy_score=0.26)
    assert decision.decision == "REJECT"
    assert decision.is_safe is False
    assert any("bão hòa" in r for r in decision.rejection_reasons)


def test_safety_policy_bypass_mode():
    """When failsafe_enabled is False, decisions are marked ACCEPT (Bypassed) and is_safe is True."""
    policy = SafetyPolicy(energy_threshold=9.04, energy_upper_threshold=22.0, entropy_threshold=0.62)
    # Energy is low (normally rejected), but failsafe_enabled=False
    decision = policy.evaluate(energy_score=3.5, entropy_score=0.20, failsafe_enabled=False)
    assert decision.decision == "ACCEPT (Bypassed)"
    assert decision.is_safe is True
    assert any("Chế độ bỏ qua" in r for r in decision.rejection_reasons)


def test_anatomical_zone_extraction():
    """Heatmap peaks correctly map to lateral and vertical lung zones."""
    # Test Right Lung Upper Zone (peak in top-left: y=50, x=50 on 512x512)
    grid = np.zeros((512, 512), dtype=np.float32)
    grid[50, 50] = 1.0
    lateral, vertical = extract_anatomical_zone_from_heatmap(grid)
    assert "phổi phải" in lateral.lower()
    assert "đỉnh phổi" in vertical.lower()

    # Test Left Lung Lower Zone (peak in bottom-right: y=450, x=450)
    grid2 = np.zeros((512, 512), dtype=np.float32)
    grid2[450, 450] = 1.0
    lateral2, vertical2 = extract_anatomical_zone_from_heatmap(grid2)
    assert "phổi trái" in lateral2.lower()
    assert "đáy phổi" in vertical2.lower()

    # Test Empty Heatmap Fallback
    lat_empty, vert_empty = extract_anatomical_zone_from_heatmap(None)
    assert "phế trường" in lat_empty.lower() or "nhu mô" in lat_empty.lower()


def test_clinical_report_generator_normal():
    """Normal scan produces clear normal findings report."""
    generator = ClinicalReportGenerator()
    preds = {d: 0.05 for d in ["Atelectasis", "Cardiomegaly", "Effusion", "Pneumonia"]}
    threshs = {d: 0.35 for d in preds}
    decision = SafetyDecision("ACCEPT", True, 12.0, 0.1)

    report = generator.generate(preds, threshs, safety_decision=decision)
    assert report.status == "GENERATED"
    assert report.is_blocked is False
    assert "Chưa phát hiện tổn thương" in report.impression


def test_clinical_report_generator_active_diseases():
    """Positive disease triggers ICD-10 code and anatomical localization."""
    generator = ClinicalReportGenerator()
    preds = {"Cardiomegaly": 0.85, "Atelectasis": 0.10}
    threshs = {"Cardiomegaly": 0.35, "Atelectasis": 0.40}
    heatmap = np.zeros((100, 100), dtype=np.float32)
    heatmap[50, 50] = 1.0  # Center (mediastinum)
    decision = SafetyDecision("ACCEPT", True, 14.0, 0.15)

    report = generator.generate(preds, threshs, heatmap=heatmap, safety_decision=decision)
    assert report.status == "GENERATED"
    assert any("Cardiomegaly" in f for f in report.findings)
    assert any("I51.7" in code for code in report.icd10_codes)
    assert "Cardiomegaly" in report.impression


def test_clinical_report_generator_rejection_lockout():
    """REJECTED scan blocks automatic report generation for patient safety."""
    generator = ClinicalReportGenerator()
    preds = {"Cardiomegaly": 0.85}
    threshs = {"Cardiomegaly": 0.35}
    decision = SafetyDecision("REJECT", False, 4.0, 0.60, ["Ảnh dị vật ngoài lồng ngực"])

    report = generator.generate(preds, threshs, safety_decision=decision)
    assert report.status == "BLOCKED"
    assert report.is_blocked is True
    assert "KHÓA AN TOÀN" in report.impression
    assert len(report.icd10_codes) == 0


def test_smart_clinical_report_guardrail_shortcut_suppression():
    """
    Smart Clinical Report Guardrail:
    When infectious disease (COVID-19 / TB) is triggered without parenchymal airspace infiltration,
    or when in_lung_ratio < 0.80, suppress false positive narrative and issue safety alert.
    """
    generator = ClinicalReportGenerator()
    preds_a = {"Infiltration": 0.20, "Consolidation": 0.25, "Pneumonia": 0.22, "Atelectasis": 0.60}
    threshs_a = {"Infiltration": 0.50, "Consolidation": 0.45, "Pneumonia": 0.45, "Atelectasis": 0.46}
    head_b = {"tb_probability": 0.84, "is_positive": True}
    head_c = {"covid_probability": 0.99, "is_positive": True}
    decision = SafetyDecision("ACCEPT", True, 14.0, 0.15)

    # Test 1: Parenchymal clear -> Suppress false positive
    report = generator.generate(
        predictions_a=preds_a,
        thresholds_a=threshs_a,
        head_b_result=head_b,
        head_c_result=head_c,
        safety_decision=decision,
    )
    assert report.status == "GENERATED"
    assert "DƯƠNG TÍNH GIẢ DO NHIỄU MÁY CHỤP / SHORTCUT" in report.impression
    assert any("CẢNH BÁO AN TOÀN AI" in f for f in report.findings)

    # Test 2: In-lung ratio < 0.80 -> Suppress false positive even if one marker is borderline
    report_xai = generator.generate(
        predictions_a=preds_a,
        thresholds_a=threshs_a,
        head_b_result=head_b,
        head_c_result=head_c,
        safety_decision=decision,
        in_lung_ratio=0.201,
    )
    assert "DƯƠNG TÍNH GIẢ DO NHIỄU MÁY CHỤP / SHORTCUT" in report_xai.impression
    assert any("20.1%" in f for f in report_xai.findings)
