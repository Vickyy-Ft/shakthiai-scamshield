# Use case

- **Pitch:** ShakthiAI ScamShield — an AI-powered cybersecurity agent that detects scams,
  phishing messages, fraudulent emails, and suspicious URLs before users fall victim to cybercrime.
- **Who it is for:** Students, families, job seekers, senior citizens, and everyday internet users
  who receive suspicious SMS messages, emails, WhatsApp forwards, fake bank alerts, or UPI payment
  requests and need a fast, trustworthy verdict.
- **Features:**
  - Paste any suspicious SMS, email, WhatsApp message, or URL and get an instant `ALLOW`, `WARN`,
    or `BLOCK` verdict from Strands Decider 2B.
  - Real confidence score and evidence displayed so users understand *why* a message is risky.
  - Amazon Bedrock explains the decision in plain language and gives actionable safety guidance.
  - Uncertain messages are flagged for human review rather than declared safe.
  - Live decision panel in the demo UI shows every policy probability as it happens.
  - Deployed on Amazon Bedrock AgentCore Runtime.
- **The decision handed to Strands Decider 2B:** classify any submitted content against the
  ScamShield policy and return `allow`, `warn`, or `block`. (`#policy`)
- **Why a decision model:** policy enforcement must be fast, cheap, consistent, and return a
  calibrated confidence the code can branch on — not a probabilistic LLM response that varies
  between runs.
- **Amazon Bedrock:** the explanation engine and the conversational interface (Amazon Nova Pro
  by default).
