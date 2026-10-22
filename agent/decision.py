"""REUSABLE DECISION PATTERN: scam and phishing policy classification  (#policy)

What it does
    Before generating any explanation, the agent submits the user's message (or URL) to
    Strands Decider 2B for a structured policy decision:

        ALLOW  – content appears safe; no immediate threat signals found.
        WARN   – suspicious signals detected; user should verify before acting.
        BLOCK  – high-confidence scam, phishing, fraud, or social-engineering content.

    Uncertain content (low confidence) is escalated to human review rather than declared
    safe, following the principle: *when in doubt, warn*.

Typed questions and options
    category (choice): which scam category the content falls under.
    violates (noul): does the content break the ScamShield policy?
    severity (score): how dangerous would acting on this content be?

Wiring
    `ScamShieldPolicy` is a thin wrapper around `decider_kit.patterns.policy.PolicyCheck`.
    `ScamShieldGuard` is a Strands `InterventionHandler` that runs before the LLM generates
    an explanation, so the explanation always matches the decider's verdict.

    In agent.py:
        guard = ScamShieldGuard(decider)
        agent = Agent(..., interventions=[guard])

How to reuse it
    Copy this file. Replace SCAM_POLICY with your own policy text, SCAM_CATEGORIES with your
    own taxonomy, and adjust the block_at / review_at thresholds. The rest of the kit
    (benchmark, demo UI, deploy, video, article) works without any further changes.
"""

from __future__ import annotations

from typing import Any

from strands.interventions import Guide, InterventionHandler, Proceed

from decider_kit import Decider
from decider_kit.patterns.policy import PolicyCheck

PATTERN_TAG = "#policy"

# ---------------------------------------------------------------------------
# Policy: the written rules Strands Decider 2B enforces
# ---------------------------------------------------------------------------
SCAM_POLICY = """
ScamShield Policy — content that must be blocked or flagged:

1. PHISHING: messages impersonating banks, payment services (UPI, PayPal, Paytm), government
   agencies (IT, UIDAI, TRAI), or courier companies that ask the user to click a link, log in,
   or verify account details.

2. FINANCIAL FRAUD: fake investment schemes, lottery wins, prize claims, "double your money"
   offers, advance-fee requests, or unsolicited requests to transfer or receive money.

3. JOB SCAMS: fraudulent job offers requiring upfront fees, requests to share bank account
   details "for salary transfer", or messages from unknown recruiters with no verifiable company.

4. SOCIAL ENGINEERING: messages that create false urgency ("Your account will be blocked in
   2 hours"), fear ("You owe taxes — pay now or face arrest"), or impersonate authority figures
   to manipulate the user into acting immediately.

5. CREDENTIAL HARVESTING: any request to share OTPs, passwords, PIN numbers, CVV codes, or
   Aadhaar / PAN details via SMS, email, link, or chat.

6. MALICIOUS URLS: links using lookalike domains (amaz0n.com), URL shorteners leading to
   unknown destinations, or links that do not match the sender's claimed identity.

Content that is genuine transactional communication, public information, or ordinary conversation
is allowed. Ambiguous content should be warned, not blocked.
""".strip()

# QUESTIONS is the typed question dict that ./kit bench and the submission checker look for.
# It mirrors the three questions PolicyCheck asks: violates (noul), category (choice), severity (score).
QUESTIONS = {
    "violates": Decider.noul(
        "Does this content violate the ScamShield policy?",
        {
            "true": "it breaks at least one rule of the policy (phishing, fraud, social engineering, credential theft, malicious URL)",
            "false": "it is a legitimate message, genuine transactional communication, or ordinary safe conversation",
        },
    ),
    "category": Decider.choice(
        "Which single scam or threat category best describes this content?",
        {
            "phishing": (
                "impersonates a bank, payment app, courier, or government body AND includes a link "
                "or asks the user to log in or verify on a website — the goal is to steal credentials via a fake site"
            ),
            "financial_fraud": (
                "promises unexpected money, a prize, lottery win, investment returns, or asks the user "
                "to pay an advance fee or transfer funds — no fake login link required"
            ),
            "job_scam": (
                "offers a job or work-from-home opportunity and asks for an upfront registration fee, "
                "security deposit, or personal bank details before any work has started"
            ),
            "social_engineering": (
                "uses urgent threats (account blocked, legal action, arrest) or authority (TRAI, IT Dept, police) "
                "to pressure the user into calling a number or acting immediately — does NOT ask for a login or money upfront"
            ),
            "credential_theft": (
                "explicitly asks the user to share an OTP, password, PIN, CVV, Aadhaar number, PAN, "
                "or other secret credential — the request for the secret IS the main goal"
            ),
            "malicious_url": (
                "contains a URL that uses a lookalike domain, URL shortener, or a domain mismatched "
                "with the claimed sender, as the primary threat indicator"
            ),
            "safe": (
                "a legitimate transactional SMS (OTP delivery, payment confirmation, bank statement), "
                "a genuine service notification, or ordinary conversation with no deceptive intent"
            ),
        },
    ),
    "severity": Decider.score(
        "How dangerous would it be if the user acted on this content as instructed?",
        ["none", "minor", "serious", "critical"],
    ),
}

SCAM_CATEGORIES: dict[str, str] = {
    "phishing":           "impersonates a bank, payment app, or government body AND includes a link to a fake login site",
    "financial_fraud":    "fake lottery, prize, investment, or advance-fee scam — promises unexpected money",
    "job_scam":           "fraudulent job offer requiring upfront fee or personal bank details before any work",
    "social_engineering": "urgent threats or authority claims that pressure the user to call or act — no fake link or money request",
    "credential_theft":   "explicitly asks the user to share OTP, password, Aadhaar, PAN, CVV, or PIN",
    "malicious_url":      "lookalike domain, URL shortener, or link mismatched with the claimed sender is the main threat",
    "safe":               "legitimate transactional message, genuine notification, or ordinary safe conversation",
}

# ---------------------------------------------------------------------------
# Policy checker (wraps the kit's generic PolicyCheck with ScamShield config)
# ---------------------------------------------------------------------------

class ScamShieldPolicy:
    """Run Strands Decider 2B against the ScamShield policy.

    Returns a `Verdict` (from decider_kit.patterns.policy) with:
        .action        → "allow" | "review" | "block"
        .category      → one of SCAM_CATEGORIES
        .p_violation   → probability that content violates the policy (0–1)
        .severity      → "none" | "minor" | "serious" | "critical"
        .confident     → True when the decider's confidence is >= 0.7
    """

    def __init__(self, decider: Decider, block_at: float = 0.65, review_at: float = 0.35):
        self._checker = PolicyCheck(
            decider,
            policy=SCAM_POLICY,
            categories=SCAM_CATEGORIES,
            block_at=block_at,
            review_at=review_at,
        )

    def check(self, content: str, context: str = "") -> Any:
        return self._checker.check(content, context=context)

    @property
    def log(self) -> list[dict[str, Any]]:
        return self._checker.log


# ---------------------------------------------------------------------------
# Strands InterventionHandler — runs before every LLM turn
# ---------------------------------------------------------------------------

_VERDICT_PREAMBLE = {
    "allow":  "✅ ALLOW",
    "review": "⚠️  WARN",
    "block":  "🚫 BLOCK",
}

_VERDICT_INSTRUCTION = {
    "allow": (
        "The ScamShield policy check returned ALLOW. "
        "The content does not appear to be a scam. "
        "Tell the user the message looks safe, but briefly mention what made it appear safe "
        "and remind them to stay vigilant."
    ),
    "review": (
        "The ScamShield policy check returned WARN. "
        "The content has suspicious signals but is not conclusively a scam. "
        "Explain what specific signals were detected, advise the user NOT to click links or share "
        "any personal information until they verify through official channels, and give concrete "
        "next steps (e.g. call the bank's official helpline, check the sender's email domain)."
    ),
    "block": (
        "The ScamShield policy check returned BLOCK. "
        "This content is highly likely to be a scam or phishing attempt. "
        "Clearly tell the user this is dangerous, explain exactly what type of threat it is, "
        "list the red flags you can see, and give firm safety instructions: do NOT click, do NOT "
        "share OTPs/passwords, report it to the relevant authority (cybercrime.gov.in in India)."
    ),
}


class ScamShieldGuard(InterventionHandler):
    """Runs Strands Decider 2B before the LLM generates an explanation.

    Injects the decider's verdict and instructions into the agent's first message so the
    LLM explanation always matches the structured decision.
    """

    name = "scamshield-policy-guard"

    def __init__(self, decider: Decider, block_at: float = 0.65, review_at: float = 0.35):
        self._policy = ScamShieldPolicy(decider, block_at=block_at, review_at=review_at)
        self.log: list[dict[str, Any]] = []
        self._last_verdict: str = "allow"

    def before_invocation(self, event, **kwargs):
        """Run the policy check before the LLM sees the message."""
        # Extract the latest user message text
        content = ""
        if event.messages:
            last = event.messages[-1]
            for block in last.get("content", []):
                if isinstance(block, dict) and "text" in block:
                    content += block["text"] + " "
        content = content.strip()
        if not content:
            return Proceed()

        verdict_obj = self._policy.check(content)
        action = verdict_obj.action  # allow | review | block

        # Build the log entry the demo UI will display
        p = verdict_obj.p_violation
        rec: dict[str, Any] = {
            "pattern":     PATTERN_TAG,
            "stage":       "policy",
            "category":    verdict_obj.category,
            "p_violation": round(p, 3),
            "severity":    verdict_obj.severity,
            "confident":   verdict_obj.confident,
            "verdict":     action,
            "decider_ms":  self._policy.log[-1].get("decider_ms", 0) if self._policy.log else 0,
        }
        self.log.append(rec)
        self._last_verdict = action

        # Guide the LLM: prepend the verdict + what to say
        instruction = (
            f"[ScamShield Decider verdict: {_VERDICT_PREAMBLE[action]} "
            f"| category: {verdict_obj.category} "
            f"| p_violation: {p:.2f} "
            f"| severity: {verdict_obj.severity}]\n\n"
            f"{_VERDICT_INSTRUCTION[action]}\n\n"
            f"Now reply to the user with this guidance. Be clear, empathetic, and practical."
        )
        return Guide(feedback=instruction)

    def before_tool_call(self, event, **kwargs):
        return Proceed()
