# ShakthiAI ScamShield 🛡️

**Think Before You Click. Stay One Step Ahead.**

An AI-powered cybersecurity agent that helps people identify scams, phishing messages, fraudulent
emails, and suspicious URLs before they fall victim to cybercrime.

Built with the **AWS User Group Madurai** Strands Decider hackathon kit.

Tags: `#strands-decider-2b` `#policy`

---

## 🚨 The problem

Fake bank alerts, fraudulent job offers, UPI scams, phishing links, and lottery frauds are among
the fastest-growing cybercrimes in India and worldwide. These attacks target students, senior
citizens, job seekers, and everyday internet users. The messages are increasingly convincing,
impersonating trusted brands and creating false urgency. Most people have no fast, trustworthy
way to verify before they act.

## ✅ What ShakthiAI does

1. **User submits** a suspicious SMS, email, WhatsApp message, or URL
2. **Strands Decider 2B** makes a structured policy decision in one forward pass:
   - `ALLOW` / `WARN` / `BLOCK`
   - Threat category (phishing, financial fraud, job scam, social engineering, credential theft, malicious URL)
   - Confidence score (0–1)
   - Severity (none, minor, serious, critical)
3. **Amazon Bedrock** (Nova Pro) explains the verdict in plain language, lists the red flags,
   and gives clear, actionable safety guidance
4. **Live decision panel** shows Strands Decider 2B probabilities in real time as the agent analyzes

## 🛡️ Decision pattern: `#policy`

The core innovation is the `ScamShieldPolicy` in `agent/decision.py` — a reusable wrapper
around `decider_kit.patterns.policy.PolicyCheck` configured with cybersecurity threat categories.

**The ScamShield policy covers:**
- **Phishing** — bank, payment service, or government agency impersonation
- **Financial fraud** — fake investments, lotteries, prizes, advance-fee scams
- **Job scams** — fraudulent job offers requiring upfront fees
- **Social engineering** — false urgency, fear tactics, authority impersonation
- **Credential theft** — requests for OTP, passwords, Aadhaar, PAN, CVV codes
- **Malicious URLs** — lookalike domains, URL shorteners, mismatched senders

**Strands Decider 2B answers three typed questions:**
- `violates` (yes/no): does this content break the ScamShield policy?
- `category` (choice): which of the six threat categories?
- `severity` (score): none / minor / serious / critical

**Thresholds:**
- `p_violation >= 0.65` → `BLOCK`
- `0.35 <= p_violation < 0.65` → `WARN` (human review)
- `p_violation < 0.35` → `ALLOW`

Uncertain content is **always flagged for human review**, never auto-declared safe — a critical
safety principle for cybersecurity agents.

## 📊 Why a decision model?

| Concern | LLM-only | Strands Decider 2B |
|---|---|---|
| **Speed** | 1–4 s per call | ~0.2 s (local), ~1.2 s (hosted) |
| **Consistency** | varies between runs | same calibrated probability every time |
| **Cost** | $0.80–$3.20 per 1,000 | ~$0.035 per 1,000 (hosted) |
| **Branch-able** | parse text response | typed probability the code branches on |
| **Privacy** | input leaves device | local mode: nothing leaves your machine |

Policy enforcement must be **fast** (every message checked), **cheap** (high volume), and
**consistent** (same message → same verdict). A decision model is the right tool for this job.

## 🏗️ Architecture

```
User message
     │
     ▼
ScamShieldGuard (InterventionHandler)
     │
     ├─── Strands Decider 2B ──→ structured policy verdict
     │       (violates, category, severity, confidence)
     │
     └─── inject verdict into Agent system instructions
          │
          ▼
       Strands Agent + Amazon Bedrock
          │
          └─── tools: analyze_message, analyze_url, get_safety_resources
               │
               ▼
            reply with explanation and safety guidance
```

## 🧪 Benchmark results

Decider: `strands-decider-2b-hobson-v19` (ugmdu hosted, CPU). LLM: Amazon Bedrock Nova Pro (`apac.amazon.nova-pro-v1:0`, ap-south-1). Test split: 12 held-out cases, 36 decisions.

| Metric | Strands Decider 2B | Amazon Bedrock Nova Pro |
|---|---|---|
| **Accuracy (test split)** | **72.2%** | 75.0% |
| `violates` accuracy | **92%** | — |
| `category` accuracy | **67%** | — |
| `severity` accuracy | **58%** | — |
| **Latency p50 per decision** | 6,363 ms | **1,971 ms** |
| Latency p95 | 6,430 ms | 2,625 ms |
| **Cost per 1,000 decisions** | **$0.035** | $0.527 |
| Confident answers (≥ 0.70) | 31% | 100% |
| **Accuracy when confident** | **100%** | 75.0% |
| Sent to human review | 69% | 0% |

**Key findings:** when the decider is confident (31% of cases), it is **100% accurate** — the LLM is 75% even at full confidence. The hosted CPU decider is **15× cheaper** than Bedrock Nova Pro. On this setup the LLM is faster (ugmdu hosted CPU vs Bedrock); with a local or GPU decider the latency reverses (~0.2 s). The 69% human-review rate is intentional: for a cybersecurity agent, uncertain messages should never be auto-approved.

## 🚀 Technology stack

- **AWS Strands Agents SDK** — agent orchestration, tool calls, intervention handlers
- **Strands Decider 2B** (`StrandsAgents/strands-decider-2B-qwen3.5-v1-2610`) — structured policy decisions
- **Amazon Bedrock** (Nova Pro) — natural-language explanations and safety guidance
- **Amazon Bedrock AgentCore Runtime** — deployment
- **Python 3.12** — agent implementation
- **FastAPI + vanilla JS** — demo web UI with live decision panel

## 📁 Repository structure

```
agent/
  agent.py          HackathonAgent class — stable chat() interface
  decision.py       REUSABLE DECISION PATTERN: ScamShieldPolicy (#policy)
  tools.py          analyze_message, analyze_url, get_safety_resources
  eval_cases.jsonl  24 labelled test cases (tune + test split)
  demo_script.yaml  video demo script with narration
  features.yaml     AgentCore Memory / Gateway toggles

decider_kit/        Reusable kit library (unchanged from UG Madurai kit)
demo/               Web UI with chat + live decision panel
deploy/             AgentCore Runtime CDK project
shakthiai_scamshield/tests/  Unit tests for tools and eval cases

submission/
  bench/            Benchmark results (accuracy, latency, cost charts)
  article/          AWS Builder Center article bundle
  video/            Demo video (under 3 minutes)
```

## 🎯 Real-world impact

**Who this helps:**
- Students receiving fake job offers on LinkedIn/WhatsApp
- Senior citizens targeted by fake bank alerts and OTP requests
- Job seekers encountering advance-fee recruitment scams
- Families forwarding suspicious WhatsApp messages
- Anyone who sees an urgent-sounding SMS and wants a second opinion before clicking

**Design principles:**
- **Fast verdict** — no waiting, no jargon
- **Clear evidence** — show exactly what makes a message suspicious
- **Actionable guidance** — tell the user what to do next (call the bank, report to cybercrime.gov.in)
- **Transparent AI** — live decision panel shows the probabilities in real time
- **Safety-first thresholds** — uncertain content gets a human-review flag, never auto-approved

## 🧩 Reusability

The `#policy` pattern in `agent/decision.py` is **immediately reusable** for any content moderation
or compliance use case:

```python
# Example: content moderation for a social platform
from decider_kit.patterns.policy import PolicyCheck
from decider_kit import Decider

moderator = PolicyCheck(
    Decider(),
    policy="Community Guidelines: no hate speech, no spam, no adult content...",
    categories={
        "hate_speech": "targets protected groups",
        "spam": "unsolicited commercial content",
        "adult": "sexually explicit material",
        "safe": "complies with guidelines",
    },
    block_at=0.7,
    review_at=0.4,
)

verdict = moderator.check(user_post)
if verdict.action == "block":
    reject_post()
elif verdict.action == "review":
    queue_for_human_review()
```

## 📝 Getting started

1. **Install dependencies:** `pip install -r requirements.txt`
2. **Set up environment:** Copy `.env.example` to `.env` and configure:
   - `DECIDER_MODE` (local | ugmdu | custom)
   - `LLM_PROVIDER` (bedrock | local | ugmdu)
   - AWS credentials for Bedrock and deployment
3. **Run tests:** `pytest shakthiai_scamshield/tests/ -v`
4. **Start demo UI:** `python demo/server.py` → http://localhost:8501
5. **Try it:** Paste a suspicious message and watch the live decision panel

## 🔐 Safety resources referenced by the agent

- **National Cyber Crime Helpline:** 1930 (24x7, India)
- **Report portal:** https://cybercrime.gov.in
- **RBI fraud reporting:** https://sachet.rbi.org.in
- **TRAI DND (spam calls/SMS):** 1909

## 📄 Licence

Apache-2.0

## 🙏 Credits

Built with the **AWS User Group Madurai** Strands Decider hackathon kit.

Uses:
- **Strands Agents** (Apache-2.0) — https://github.com/StrandsLabs/strands-agents
- **Strands Decider 2B** (Apache-2.0) — https://github.com/strands-labs/strands-decider

This is not an official AWS project.

---

**ShakthiAI ScamShield — Think Before You Click. Stay One Step Ahead. 🛡️**
