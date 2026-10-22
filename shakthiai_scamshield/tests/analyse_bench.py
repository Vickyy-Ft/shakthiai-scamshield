"""Analyse tune-split bench results to guide question tuning.
Run: python shakthiai_scamshield/tests/analyse_bench.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
data = json.loads((ROOT / "submission" / "bench" / "results.json").read_text(encoding="utf-8"))
rows = data["rows"]

print("=== Per-question accuracy on tune split ===\n")
per_q: dict = {"violates": [], "category": [], "severity": []}

for r in rows:
    exp = r["expected"]
    dec = r["decider"]
    for q in per_q:
        if q not in exp:
            continue
        got = dec[q]["label"]
        expected = exp[q]
        correct = got == expected
        per_q[q].append(correct)
        if not correct:
            conf = dec[q]["confidence"]
            state_preview = str(r.get("i", "?"))
            print(f"  MISS [{q}]  expected={expected!r:22s} got={got!r:22s}  conf={conf:.3f}  row={r['i']}")

print()
for q, vals in per_q.items():
    acc = sum(vals) / len(vals) if vals else 0
    print(f"  {q:12s}: {sum(vals)}/{len(vals)} = {acc:.0%}")

print()
print("=== Observations ===")
print("violates:  The decider is good at this (high confidence, high accuracy).")
print("category:  Confusing phishing vs social_engineering; job_scam sometimes miscategorised.")
print("severity:  Confidence is low across all rows (~0.3). severity needs richer option wording.")
print()
print("=== Tuning recommendations ===")
print("1. Improve 'category' option wording to sharply distinguish phishing from social_engineering.")
print("2. For 'severity', add concrete examples per level to raise confidence.")
print("3. For safe messages, the category question may need a 'safe' anchor that is more explicit.")
