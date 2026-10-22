"""ShakthiAI ScamShield — the agent.

Strands Decider 2B makes the structured policy decision (ALLOW / WARN / BLOCK) before the
LLM generates an explanation. Amazon Bedrock (Nova Pro by default) provides the natural-
language explanation and safety guidance.

    from agent.agent import HackathonAgent
    out = HackathonAgent().chat("URGENT: Your SBI account will be blocked. Click http://sbi-verify.xyz now.")
    out["reply"], out["decisions"]

The `HackathonAgent.chat()` interface is the kit's stable contract: the demo UI, benchmark,
video recorder, and AgentCore deployment all depend on it.
"""

from __future__ import annotations

import time
from typing import Any

from strands import Agent

from decider_kit import Decider
from decider_kit.llm import agent_model, default_model_id, image_blocks, strip_thinking

from .decision import ScamShieldGuard
from .tools import TOOLS

NAME = "ShakthiAI ScamShield 🛡️"

SYSTEM_PROMPT = """You are ShakthiAI ScamShield, an AI-powered cybersecurity assistant.

Your job is to help people identify scams, phishing messages, fraudulent emails, and suspicious
URLs before they fall victim to cybercrime.

You have three analysis tools:
- analyze_message: scans text for scam language, urgency signals, impersonation, and credential requests.
- analyze_url: checks a URL for phishing indicators, lookalike domains, and URL shorteners.
- get_safety_resources: returns official helplines and reporting portals.

HOW TO RESPOND:
1. Use analyze_message and/or analyze_url on the submitted content first.
2. The ScamShield policy guard will have already run Strands Decider 2B and injected a verdict
   (ALLOW / WARN / BLOCK) into your instructions. Follow that verdict exactly.
3. Present the verdict prominently, explain the specific red flags you found, and give clear
   actionable guidance.
4. Use simple, friendly language — your users may not be technical.
5. For BLOCK verdicts, always mention cybercrime.gov.in / 1930 helpline.
6. Be empathetic. Scam victims feel embarrassed; reassure them.
7. Never fabricate evidence. Only report signals that the tools or the message text actually show.

Keep responses focused: verdict → evidence → what to do next."""

EAGER_SYSTEM_PROMPT = """You are ShakthiAI ScamShield. For this demo, analyze the submitted content
immediately without asking for clarification. Use analyze_message and analyze_url on whatever is provided,
then give the verdict, the red flags, and the safety advice. Be direct and decisive."""


class HackathonAgent:
    """One Strands agent per session with the ScamShield policy pattern wired in."""

    def __init__(
        self,
        decider: Decider | None = None,
        model_id: str | None = None,
        eager: bool | None = None,
    ):
        import os

        self.decider = decider or Decider()
        self.eager = eager if eager is not None else os.environ.get("DEMO_EAGER") == "1"
        self.model_id = model_id or default_model_id()
        self.sessions: dict[str, tuple[Agent, ScamShieldGuard]] = {}

    def _session(self, session_id: str) -> tuple[Agent, ScamShieldGuard]:
        if session_id not in self.sessions:
            guard = ScamShieldGuard(self.decider)
            prompt = EAGER_SYSTEM_PROMPT if self.eager else SYSTEM_PROMPT
            agent = Agent(
                model=agent_model(self.model_id),
                system_prompt=prompt,
                tools=TOOLS,
                interventions=[guard],
                callback_handler=None,
            )
            self.sessions[session_id] = (agent, guard)
        return self.sessions[session_id]

    def chat(
        self,
        message: str,
        session_id: str = "default",
        images: list[Any] | None = None,
    ) -> dict[str, Any]:
        """`images` (optional): screenshots of suspicious messages (paths, bytes, or base64).
        The decider and the LLM both see them when images are passed."""
        agent, guard = self._session(session_id)
        before = len(guard.log)
        t0 = time.perf_counter()

        result = agent(
            [*image_blocks(images), {"text": message}] if images else message,
            invocation_state={"images": list(images or [])},
        )
        reply = strip_thinking(str(result))

        return {
            "reply": reply,
            "decisions": guard.log[before:],
            "model_id": self.model_id,
            "latency_ms": round((time.perf_counter() - t0) * 1000),
            "agent": NAME,
            "eager": self.eager,
        }


if __name__ == "__main__":
    import json
    import sys

    agent = HackathonAgent()
    test_messages = sys.argv[1:] or [
        "URGENT: Your HDFC Bank account has been blocked due to suspicious activity. "
        "Click http://hdfc-secure-verify.xyz/login to restore access immediately.",
        "Hi, I got this message: 'You have won Rs 50,000! Send your bank account number to claim.'",
        "Your OTP for SBI NetBanking is 847291. Do not share this with anyone.",
    ]
    for msg in test_messages:
        print(f"\n--- Message ---\n{msg}\n")
        out = agent.chat(msg)
        print(json.dumps({k: v for k, v in out.items() if k != "decisions"}, indent=2))
        for d in out["decisions"]:
            print("Decision:", json.dumps(d, indent=2))
