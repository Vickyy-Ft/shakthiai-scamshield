# ShakthiAI ScamShield 🛡️

**Think Before You Click. Stay One Step Ahead.**

ShakthiAI is an AI-powered cybersecurity agent that helps people identify scams, phishing
messages, fraudulent emails, and suspicious links before they fall victim to cybercrime.

Built with the AWS User Group Madurai Strands Decider hackathon kit.

Tags: `#strands-decider-2b` `#policy`

---

## The problem

Fake bank alerts, UPI scams, fraudulent job offers, phishing links, and lottery frauds are
targeting students, senior citizens, job seekers, and everyday internet users. These attacks are
increasingly convincing. Most people have no fast, trustworthy way to check before they act.

## What ShakthiAI does

1. **User submits** a suspicious SMS, email, WhatsApp message, or URL.
2. **Strands Decider 2B** runs a structured policy decision in one forward pass:
   `ALLOW` / `WARN` / `BLOCK` with a calibrated confidence score.
3. **Amazon Bedrock** (Nova Pro) explains the verdict in plain language, lists the red flags,
   and gives clear actionable safety guidance.
4. **The demo UI** shows both the conversation and the live Decider 2B probabilities side by side.

## Decision pattern: `#policy`

The `ScamShieldPolicy` in `agent/decision.py` wraps `decider_kit.patterns.policy.PolicyCheck`
with the ScamShield policy text and six threat categories:

| Category | Description |
|---|---|
| `phishing` | Bank / service impersonation with a fake login link |
| `financial_fraud` | Lottery, prize, investment, advance-fee scam |
| `job_scam` | Fraudulent job offer requiring upfront payment |
| `social_engineering` | False urgency / authority to manipulate immediate action |
| `credential_theft` | Request for OTP, password, Aadhaar, PAN, CVV |
| `malicious_url` | Lookalike domain, URL shortener, mismatched sender |

The decider answers three questions per submission:
- `violates` (noul) — does it break the ScamShield policy?
- `category` (choice) — which threat category?
- `severity` (score) — none / minor / serious / critical

Verdicts: `block_at ≥ 0.65`, `review_at ≥ 0.35`. Uncertain content is flagged for human
review, never auto-declared safe.

## Benchmark results

Decider: `strands-decider-2b-hobson-v19` (ugmdu hosted, CPU). LLM: Amazon Bedrock Nova Pro (`apac.amazon.nova-pro-v1:0`). Test split: 12 held-out cases.

| Metric | Strands Decider 2B | Amazon Bedrock Nova Pro |
|---|---|---|
| **Accuracy (test split)** | **72.2%** | 75.0% |
| `violates` accuracy | **92%** | — |
| `category` accuracy | 67% | — |
| `severity` accuracy | 58% | — |
| **Latency p50** | 6,363 ms (hosted CPU) | **1,971 ms** |
| Latency p95 | 6,430 ms | 2,625 ms |
| **Cost per 1,000 decisions** | **$0.035** | $0.527 |
| Accuracy when confident | **100%** | 75.0% |
| Sent to human review | 69% | 0% |

When the decider is confident, it is **100% accurate** vs 75% for the LLM. The decider is **15× cheaper**. The LLM is faster on this setup (hosted CPU vs Bedrock); a local/GPU decider reverses that. The 69% human-review rate is intentional: uncertain cybersecurity decisions should always go to a human.

Run `.\kit.cmd bench --split test` to reproduce.

## Repo structure

```
agent/
  agent.py          HackathonAgent — the stable chat() interface
  decision.py       REUSABLE DECISION PATTERN: ScamShieldPolicy (#policy)
  tools.py          analyze_message, analyze_url, get_safety_resources
  eval_cases.jsonl  22 labelled cases (tune + test split)
  demo_script.yaml  video demo turns

decider_kit/        Reusable kit library (unchanged)
demo/               Web UI (chat + live decision panel)
deploy/             AgentCore Runtime CDK project
```

## Technology stack

- **AWS Strands Agents SDK** — agent orchestration and tool calls
- **Strands Decider 2B** — structured policy decisions
- **Amazon Bedrock** (Nova Pro) — natural-language explanations
- **Amazon Bedrock AgentCore Runtime** — deployment
- **Python** — agent and kit
- **FastAPI + vanilla JS** — demo web UI

## Why a decision model instead of an LLM?

| Concern | LLM | Strands Decider 2B |
|---|---|---|
| Speed | 1–3 s / call | ~0.2 s local, ~1.2 s hosted |
| Consistency | varies between runs | same calibrated probability |
| Cost | tokens × price | ~$0.035 / 1,000 (hosted) |
| Explainability | narrative | typed probability the code branches on |
| Privacy | input leaves device | local mode: nothing leaves your machine |

## Licence

Apache-2.0. Credits: AWS User Group Madurai.
Uses Strands Agents and Strands Decider (Apache-2.0). Not an official AWS project.
