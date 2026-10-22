"""Unit tests for ShakthiAI ScamShield tools — no cloud calls, no Decider needed.

These tests import the tool logic directly (bypassing the @tool decorator) so they work
without strands-agents installed in the test environment.

Run: pytest shakthiai_scamshield/tests/test_tools.py -v
"""
from __future__ import annotations

import sys
import re
import urllib.parse
from pathlib import Path

# Make sure the workspace root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# ── Import the pure logic from tools.py without triggering @tool ───────────
# We import the module's private helpers directly so the tests don't need strands.
import importlib, types

# Stub the 'strands' module so tools.py can be imported without the package
if "strands" not in sys.modules:
    strands_stub = types.ModuleType("strands")
    strands_stub.tool = lambda fn=None, **kw: (fn if fn else lambda f: f)  # type: ignore[assignment]
    sys.modules["strands"] = strands_stub

import agent.tools as _tools


def _call(fn, *args, **kwargs):
    """Call a Strands @tool function whether it is wrapped or not."""
    raw = getattr(fn, "func", fn)
    return raw(*args, **kwargs)


# ── analyze_url ────────────────────────────────────────────────────────────

class TestAnalyzeUrl:
    def test_known_phishing_url(self):
        result = _call(_tools.analyze_url, "http://hdfc-kyc-verify.xyz/login")
        assert result["risk_level"] in ("high", "medium")
        assert result["signal_count"] >= 1

    def test_url_shortener_detected(self):
        result = _call(_tools.analyze_url, "https://bit.ly/free-iphone")
        assert result["risk_level"] in ("high", "medium")
        # signal text will contain the matched text "bit.ly"
        assert any("bit.ly" in s for s in result["suspicious_signals"])

    def test_ip_address_url(self):
        result = _call(_tools.analyze_url, "http://192.168.1.1/banking/login")
        assert result["risk_level"] in ("high", "medium")

    def test_brand_in_path_not_domain(self):
        result = _call(_tools.analyze_url, "https://secure-amazon-verify.com/account")
        assert result["signal_count"] >= 1

    def test_legitimate_url_low_risk(self):
        result = _call(_tools.analyze_url, "https://www.icicibank.com/manage-your-account/my-account.html")
        assert result["risk_level"] in ("low", "medium")

    def test_high_abuse_tld(self):
        result = _call(_tools.analyze_url, "http://prize-claim.tk/win")
        assert result["risk_level"] in ("high", "medium")

    def test_suspicious_credential_path(self):
        result = _call(_tools.analyze_url, "http://example.com/verify-account/update-info")
        assert result["signal_count"] >= 1

    def test_returns_domain(self):
        result = _call(_tools.analyze_url, "https://cybercrime.gov.in/report")
        assert "domain" in result
        assert "cybercrime.gov.in" in result["domain"]


# ── analyze_message ────────────────────────────────────────────────────────

class TestAnalyzeMessage:
    def test_otp_request_detected(self):
        result = _call(_tools.analyze_message,
            "Please share your OTP immediately to verify your SBI account. "
            "Your account will be blocked in 2 hours if not verified.")
        assert result["credential_request_signals"] >= 1
        assert result["urgency_signals"] >= 1
        assert result["risk_level"] in ("high", "medium")

    def test_lottery_scam(self):
        result = _call(_tools.analyze_message,
            "Congratulations! You have won Rs 1,00,000 in Amazon Lucky Draw. "
            "Click http://amaz0n-reward.tk to claim your prize. Offer expires today!")
        assert result["total_signal_count"] >= 3
        assert result["risk_level"] == "high"

    def test_bank_impersonation(self):
        result = _call(_tools.analyze_message,
            "URGENT: Your HDFC Bank account has been suspended. "
            "Verify your KYC at the link below immediately.")
        assert result["impersonation_signals"] >= 1
        assert result["urgency_signals"] >= 1

    def test_genuine_transaction_low_risk(self):
        result = _call(_tools.analyze_message,
            "Your UPI transaction of Rs 500 to Swiggy is successful. "
            "Transaction ID: UPI20261022-98765. For queries contact 1800-120-1740.")
        assert result["risk_level"] == "low"

    def test_credential_theft_aadhaar(self):
        result = _call(_tools.analyze_message,
            "Your Aadhaar card is linked to suspicious activity. "
            "Share your Aadhaar number and OTP to avoid arrest.")
        assert result["credential_request_signals"] >= 1

    def test_job_scam_upfront_fee(self):
        result = _call(_tools.analyze_message,
            "Work from home earn Rs 5000 per day. No experience needed. "
            "Pay Rs 999 registration fee to start. WhatsApp 9876543210.")
        assert result["total_signal_count"] >= 2

    def test_urls_extracted(self):
        result = _call(_tools.analyze_message,
            "Click here to verify: https://phish.example.com/login or www.scam.tk")
        assert len(result["urls_found"]) >= 1

    def test_empty_message(self):
        result = _call(_tools.analyze_message, "Hi, how are you?")
        assert result["risk_level"] == "low"
        assert result["total_signal_count"] == 0


# ── get_safety_resources ───────────────────────────────────────────────────

class TestGetSafetyResources:
    def test_returns_helpline(self):
        result = _call(_tools.get_safety_resources)
        assert "1930" in result["national_helpline"]

    def test_returns_cybercrime_portal(self):
        result = _call(_tools.get_safety_resources)
        assert "cybercrime.gov.in" in result["cybercrime_portal"]

    def test_returns_all_tips(self):
        result = _call(_tools.get_safety_resources)
        for key in ("tip_never_share", "tip_verify", "tip_url", "tip_urgency"):
            assert key in result
            assert len(result[key]) > 10


# ── eval_cases.jsonl structure ─────────────────────────────────────────────

class TestEvalCases:
    def test_cases_load(self):
        import json
        cases_path = Path(__file__).resolve().parent.parent.parent / "agent" / "eval_cases.jsonl"
        rows = [json.loads(l) for l in cases_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(rows) >= 24, f"need 24+ eval cases, got {len(rows)}"

    def test_cases_have_required_fields(self):
        import json
        cases_path = Path(__file__).resolve().parent.parent.parent / "agent" / "eval_cases.jsonl"
        rows = [json.loads(l) for l in cases_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        for i, row in enumerate(rows):
            assert "state" in row, f"row {i} missing 'state'"
            assert "expected" in row, f"row {i} missing 'expected'"
            assert "split" in row, f"row {i} missing 'split'"

    def test_tune_test_split(self):
        import json
        cases_path = Path(__file__).resolve().parent.parent.parent / "agent" / "eval_cases.jsonl"
        rows = [json.loads(l) for l in cases_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        test_rows = [r for r in rows if r.get("split") == "test"]
        tune_rows = [r for r in rows if r.get("split") == "tune"]
        assert len(test_rows) >= 12, f"need 12+ test cases, got {len(test_rows)}"
        assert len(tune_rows) >= 8, f"need 8+ tune cases, got {len(tune_rows)}"

    def test_expected_labels_valid(self):
        import json
        cases_path = Path(__file__).resolve().parent.parent.parent / "agent" / "eval_cases.jsonl"
        rows = [json.loads(l) for l in cases_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        valid_violates = {"yes", "no"}
        valid_categories = {
            "phishing", "financial_fraud", "job_scam",
            "social_engineering", "credential_theft", "malicious_url", "safe",
        }
        valid_severity = {"none", "minor", "serious", "critical"}
        for i, row in enumerate(rows):
            exp = row["expected"]
            if "violates" in exp:
                assert exp["violates"] in valid_violates, f"row {i}: bad violates={exp['violates']}"
            if "category" in exp:
                assert exp["category"] in valid_categories, f"row {i}: bad category={exp['category']}"
            if "severity" in exp:
                assert exp["severity"] in valid_severity, f"row {i}: bad severity={exp['severity']}"


# ── eval_cases.jsonl structure ─────────────────────────────────────────────

class TestEvalCases:
    def test_cases_load(self):
        import json
        cases_path = Path(__file__).resolve().parent.parent.parent / "agent" / "eval_cases.jsonl"
        rows = [json.loads(l) for l in cases_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(rows) >= 24, f"need 24+ eval cases, got {len(rows)}"

    def test_cases_have_required_fields(self):
        import json
        cases_path = Path(__file__).resolve().parent.parent.parent / "agent" / "eval_cases.jsonl"
        rows = [json.loads(l) for l in cases_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        for i, row in enumerate(rows):
            assert "state" in row, f"row {i} missing 'state'"
            assert "expected" in row, f"row {i} missing 'expected'"
            assert "split" in row, f"row {i} missing 'split'"

    def test_tune_test_split(self):
        import json
        cases_path = Path(__file__).resolve().parent.parent.parent / "agent" / "eval_cases.jsonl"
        rows = [json.loads(l) for l in cases_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        test_rows = [r for r in rows if r.get("split") == "test"]
        tune_rows = [r for r in rows if r.get("split") == "tune"]
        assert len(test_rows) >= 12, f"need 12+ test cases, got {len(test_rows)}"
        assert len(tune_rows) >= 8, f"need 8+ tune cases, got {len(tune_rows)}"

    def test_expected_labels_valid(self):
        import json
        cases_path = Path(__file__).resolve().parent.parent.parent / "agent" / "eval_cases.jsonl"
        rows = [json.loads(l) for l in cases_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        valid_violates = {"yes", "no"}
        valid_categories = {
            "phishing", "financial_fraud", "job_scam",
            "social_engineering", "credential_theft", "malicious_url", "safe",
        }
        valid_severity = {"none", "minor", "serious", "critical"}
        for i, row in enumerate(rows):
            exp = row["expected"]
            if "violates" in exp:
                assert exp["violates"] in valid_violates, f"row {i}: bad violates={exp['violates']}"
            if "category" in exp:
                assert exp["category"] in valid_categories, f"row {i}: bad category={exp['category']}"
            if "severity" in exp:
                assert exp["severity"] in valid_severity, f"row {i}: bad severity={exp['severity']}"
