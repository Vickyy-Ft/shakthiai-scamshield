# ShakthiAI ScamShield — Think Before You Click

## The problem

Phishing messages, UPI scams, fake lottery wins, fraudulent job offers, and impersonation texts
targeting bank customers are among the fastest-growing cybercrimes affecting everyday users in
India and worldwide. Most victims are not technically savvy. They receive an urgent-sounding SMS,
see a familiar brand name, and act before verifying. By the time they realize the mistake, their
credentials are stolen or their money is gone.

Existing solutions are either too technical, too slow, or require users to already know what a
scam looks like. We wanted to build something different: a safety layer that works like an
informed friend — fast, clear, and actionable.

## What ShakthiAI does

ShakthiAI ScamShield lets users paste any suspicious SMS, email, WhatsApp message, or URL into
a chat interface. The agent analyses the content and returns:

- A **structured verdict**: `ALLOW`, `WARN`, or `BLOCK`
- The **threat category**: phishing, financial fraud, job scam, social engineering,
  credential theft, or malicious URL
- A **confidence score** from Strands Decider 2B
- A **plain-language explanation** from Amazon Bedrock with specific red flags and next steps

< FIGURE 1: Demo UI showing a phishing message verdict — BLOCK with probabilities >

## How it works

The architecture separates two concerns cleanly:

1. **Strands Decider 2B** makes the structured policy decision. It reads the message and answers
   three typed questions in a single forward pass:
   - `violates` (yes/no): does the content break the ScamShield policy?
   - `category` (choice): which of the six threat categories does it fall under?
   - `severity` (score): how dangerous is acting on this — none, minor, serious, or critical?

2. **Amazon Bedrock** (Nova Pro) receives the verdict, the category, the probability, and the
   severity as part of its system instructions. It then generates the explanation and safety
   advice in simple language the user can act on immediately.

The `ScamShieldGuard` is a Strands `InterventionHandler` that runs `before_invocation` — before
the LLM generates any text. This ensures the explanation always matches the decider's verdict,
not the other way around.

< FIGURE 2: Architecture diagram — message → Decider 2B policy check → Bedrock explanation >

## The reusable decision pattern: #policy

The `ScamShieldPolicy` class in `agent/decision.py` wraps `decider_kit.patterns.policy.PolicyCheck`
with a cybersecurity-specific policy and six threat categories. Any developer can copy it, replace
the policy text and category list, and have the same structured enforcement in their own agent.

```python
# Reuse example: adapt the policy and categories for your domain
from decider_kit.patterns.policy import PolicyCheck
from decider_kit import Decider

checker = PolicyCheck(
    Decider(),
    policy="Your policy text here...",
    categories={"safe": "...", "harmful": "..."},
    block_at=0.65,
    review_at=0.35,
)
verdict = checker.check(user_message)
# verdict.action → "allow" | "review" | "block"
# verdict.p_violation, verdict.category, verdict.severity
```

The thresholds encode a safety-first principle: uncertain content (`review_at ≤ p < block_at`)
is flagged for human review rather than declared safe. In cybersecurity, a false negative
(missing a scam) is more costly than a false positive (warning the user unnecessarily).

## Benchmark results

We benchmarked Strands Decider 2B against Amazon Bedrock (Nova Pro) on the same 24 labelled
cases using `./kit bench`.

< FIGURE 3: Accuracy chart — decider vs LLM on the test split >

< FIGURE 4: Latency chart — p50 and p95 per decision >

Key findings (test split, `strands-decider-2b-hobson-v19` on hosted CPU vs Amazon Bedrock Nova Pro `apac.amazon.nova-pro-v1:0`):

| Metric | Strands Decider 2B | Amazon Bedrock Nova Pro |
|---|---|---|
| **Accuracy** | **72.2%** | 75.0% |
| `violates` accuracy | **92%** | — |
| `category` accuracy | 67% | — |
| `severity` accuracy | 58% | — |
| **Latency p50** | 6,363 ms | **1,971 ms** |
| **Cost per 1,000** | **$0.035** | $0.527 |
| Accuracy when confident | **100%** | 75.0% |
| Human review rate | 69% | 0% |

The hosted CPU decider is **15× cheaper** than Bedrock Nova Pro. When the decider is confident, it achieves **100% accuracy** — outperforming the LLM at 75%. On this setup the LLM is faster (hosted CPU vs Bedrock); with a local GPU or Apple silicon decider, latency drops to ~0.2 s. The 69% human-review rate is intentional: uncertain cybersecurity decisions should always escalate to a human rather than be auto-approved.

The decider's advantage in this use case: policy enforcement must be consistent. An LLM
might describe the same phishing message differently on two consecutive calls. The decider
returns the same calibrated probability every time.

## Technology stack

- **AWS Strands Agents SDK** — agent orchestration, tool calls, and the InterventionHandler wiring
- **Strands Decider 2B** (`StrandsAgents/strands-decider-2B-qwen3.5-v1-2610`) — structured policy decisions
- **Amazon Bedrock** (Nova Pro) — natural-language explanations and safety guidance
- **Amazon Bedrock AgentCore Runtime** — deployment
- **Python** + **FastAPI** + **vanilla JavaScript** — agent and demo web UI

## Impact

ShakthiAI is designed for people who are not cybersecurity professionals: students receiving fake
job offers, senior citizens targeted by fake bank alerts, families getting forwarded WhatsApp
scam messages. The verdict is immediate and the guidance is plain. The live decision panel in
the demo shows the probabilities in real time, making the AI reasoning transparent.

The architecture is also directly reusable: any developer building a content moderation agent,
a compliance tool, or a safety filter can adopt the `#policy` pattern and the `ScamShieldPolicy`
class without modification to the kit infrastructure.

---

Built with the AWS User Group Madurai Strands Decider hackathon kit.
Tags: `#strands-decider-2b` `#policy`
