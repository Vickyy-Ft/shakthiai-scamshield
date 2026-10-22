"""ShakthiAI ScamShield tools — content analysis helpers.

These tools give the LLM structured signals it can use alongside the decider's verdict.
They are read-only and do not perform any irreversible action, so no additional guardrail
is needed on the tool calls themselves (the policy decision runs before_invocation).

Keep a clear one-line docstring on each: the LLM reads it, and the tool-selection pattern
uses it as the option description.
"""

from __future__ import annotations

import re
import urllib.parse
from strands import tool


# ---------------------------------------------------------------------------
# URL analysis
# ---------------------------------------------------------------------------

# Common lookalike TLD and domain tricks used in phishing
_SUSPICIOUS_PATTERNS = [
    r"@",                        # URL with embedded credentials
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",   # raw IP address
    r"bit\.ly|tinyurl|t\.co|goo\.gl|ow\.ly|short\.gy|rb\.gy|is\.gd|cutt\.ly",  # URL shorteners
    r"[a-z0-9]+-[a-z0-9]+-[a-z0-9]+\.",      # hyphen-heavy subdomains
    r"\.xyz|\.tk|\.ml|\.ga|\.cf|\.gq",        # high-abuse TLDs
    r"secure[_-]?login|verify[_-]?account|update[_-]?info|confirm[_-]?identity",
    r"paypal|amazon|apple|google|microsoft|netflix|hdfc|sbi|icici|paytm|phonepe",  # brand names in path
]

_URGENT_WORDS = [
    "urgent", "immediately", "action required", "your account", "suspended",
    "verify now", "click here", "limited time", "expires", "otp", "password",
    "blocked", "arrested", "penalty", "fine", "aadhaar", "pan card", "kyc",
    "won", "prize", "lottery", "selected", "congratulations", "job offer",
    "work from home", "earn", "invest", "double", "free", "reward",
]


@tool
def analyze_url(url: str) -> dict:
    """Analyze a URL for phishing and malicious indicators: domain, shortener use, suspicious patterns."""
    url = url.strip()
    signals: list[str] = []
    try:
        parsed = urllib.parse.urlparse(url if "://" in url else "https://" + url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        path = parsed.path.lower()
        full = url.lower()

        for pat in _SUSPICIOUS_PATTERNS:
            m = re.search(pat, full, re.I)
            if m:
                signals.append(f"pattern match: {m.group(0)[:50]}")

        # Check if a known brand name appears in the path/subdomain but not as the root domain
        brand_match = re.search(
            r"(paypal|amazon|apple|google|microsoft|hdfc|sbi|icici|paytm|phonepe|uidai|incometax)",
            full, re.I
        )
        root = domain.split(".")[-2] if domain.count(".") >= 1 else domain
        if brand_match and brand_match.group(1).lower() not in root.lower():
            signals.append(f"brand '{brand_match.group(1)}' in URL but root domain is '{root}'")

        # HTTPS check
        uses_https = url.lower().startswith("https://")

        return {
            "url": url,
            "domain": domain,
            "uses_https": uses_https,
            "suspicious_signals": signals,
            "signal_count": len(signals),
            "risk_level": "high" if len(signals) >= 3 else "medium" if len(signals) >= 1 else "low",
        }
    except Exception as e:
        return {"url": url, "error": str(e), "risk_level": "unknown"}


@tool
def analyze_message(text: str) -> dict:
    """Scan a message text for scam language patterns: urgency, credential requests, impersonation signals."""
    text_lower = text.lower()
    found_urgent = [w for w in _URGENT_WORDS if w in text_lower]

    # Detect credential requests
    credential_patterns = [
        r"otp|one.time.passw", r"password|passcode", r"cvv|cvc",
        r"aadhaar|aadhar", r"pan\s*(card|number)?", r"account\s*number",
        r"pin\s*number", r"card\s*number", r"expiry",
    ]
    credential_signals = [p for p in credential_patterns if re.search(p, text_lower)]

    # Detect urgency patterns
    urgency_patterns = [
        r"\d+\s*(hour|minute|min|hr)s?\s*(left|remaining|only)",
        r"expires?\s*(in|at|on)",
        r"last\s*(chance|opportunity|warning)",
        r"immediately|right\s*now|asap",
        r"block(ed)?|suspend(ed)?|terminat(ed)?|deactivat(ed)?",
    ]
    urgency_signals = [p for p in urgency_patterns if re.search(p, text_lower)]

    # Detect impersonation
    impersonation_patterns = [
        r"\b(hdfc|sbi|icici|axis|kotak|rbl)\s*(bank)?",
        r"\b(paytm|phonepe|gpay|google\s*pay|amazon\s*pay|bhim)\b",
        r"\b(uidai|aadhar|aadhaar)\b",
        r"\b(income\s*tax|it\s*department|cbdt)\b",
        r"\b(trai|telecom)\b",
        r"\b(rbi|reserve\s*bank)\b",
        r"\b(fedex|dhl|bluedart|india\s*post|ecom\s*express)\b",
        r"\b(amazon|flipkart|myntra|snapdeal)\b",
    ]
    impersonation_signals = [p for p in impersonation_patterns if re.search(p, text_lower)]

    # Count suspicious URLs in the text
    urls = re.findall(r"https?://[^\s]+|www\.[^\s]+", text, re.I)

    total_signals = len(found_urgent) + len(credential_signals) + len(urgency_signals) + len(impersonation_signals)

    return {
        "length": len(text),
        "urgent_words_found": found_urgent[:8],  # cap display
        "credential_request_signals": len(credential_signals),
        "urgency_signals": len(urgency_signals),
        "impersonation_signals": len(impersonation_signals),
        "urls_found": urls[:3],
        "total_signal_count": total_signals,
        "risk_level": "high" if total_signals >= 5 else "medium" if total_signals >= 2 else "low",
    }


@tool
def get_safety_resources() -> dict:
    """Return official cybersecurity resources and helpline numbers for reporting scams in India."""
    return {
        "cybercrime_portal": "https://cybercrime.gov.in",
        "national_helpline": "1930 (Cyber Crime Helpline, 24x7)",
        "rbi_fraud_reporting": "sachet.rbi.org.in",
        "trai_dnd": "1909 (stop spam calls/SMS)",
        "cert_in": "https://www.cert-in.org.in",
        "tip_never_share": "Never share OTPs, passwords, CVV, Aadhaar, or PAN with anyone — banks never ask.",
        "tip_verify": "Always call the official helpline (printed on your card/passbook) to verify any request.",
        "tip_url": "Before clicking, hover over a link to check the real URL. When in doubt, do not click.",
        "tip_urgency": "Scammers create false urgency. If a message says 'act now or lose access', that is a red flag.",
    }


TOOLS = [analyze_url, analyze_message, get_safety_resources]
