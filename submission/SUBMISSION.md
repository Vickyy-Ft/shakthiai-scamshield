# Submission: Agent Experience Hackathon (Strands Decider)

Submit before **23 October 2026, 11:59 p.m. PT** on the hackathon page.

- Repository: https://github.com/Vickyy-Ft/shakthiai-scamshield
- Video: <paste the public YouTube/Vimeo link after uploading your screen recording>
- Article: <paste the AWS Builder Center link after publishing submission/article/>
- Tags: #strands-decider-2b #policy
- Agent on AWS: (running on Amazon Bedrock apac.amazon.nova-pro-v1:0, ap-south-1)

## What's done ✅

- [x] Agent built: ShakthiAI ScamShield (`agent/`)
- [x] Strands Decider 2B wired via `ScamShieldGuard` (`#policy` pattern)
- [x] Amazon Bedrock connected (`apac.amazon.nova-pro-v1:0`, ap-south-1)
- [x] Benchmark run: 72.2% accuracy, 100% when confident, $0.035/1000 vs $0.527 LLM
- [x] Reusable decision pattern labelled in `agent/decision.py`
- [x] 24 labelled eval cases (12 tune / 12 test)
- [x] Demo UI ready (`.\kit.cmd demo` → http://localhost:8501)
- [x] Article drafted (`submission/article/body.md`)
- [x] Repo pushed: https://github.com/Vickyy-Ft/shakthiai-scamshield
- [x] Apache-2.0 licence included

## Still to do by hand 📋

1. **Screen-record the demo video** (under 3 minutes):
   - Run `.\kit.cmd demo` → open http://localhost:8501
   - Use Xbox Game Bar (Win + G) or OBS to record
   - Show these 4 turns:
     1. HDFC phishing → BLOCK verdict in panel
     2. Amazon lottery scam → BLOCK
     3. Genuine UPI transaction → ALLOW
     4. "What if I already clicked?" → recovery guidance
   - Upload to YouTube as **Public**
   - Paste the link above in this file

2. **Publish the article on AWS Builder Center**:
   - Title, description, tags from `submission/article/fields.md`
   - Body from `submission/article/body.md`
   - Upload bench charts at `< FIGURE n >` markers
   - Tags: `strands-decider-2b` and `policy`
   - Paste the article URL above

3. **Submit on the hackathon page** (builder.aws.com):
   - GitHub repo: https://github.com/Vickyy-Ft/shakthiai-scamshield
   - Article URL
   - Video URL
   - Tags: #strands-decider-2b #policy
