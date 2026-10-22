"""Quick static validation — run without strands installed."""
import ast, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ok = True

def check(name, cond):
    global ok
    status = "PASS" if cond else "FAIL"
    if not cond:
        ok = False
    print(f"  {status}  {name}")

print("=== decision.py ===")
src = (ROOT / "agent" / "decision.py").read_text(encoding="utf-8")
tree = ast.parse(src)
doc = ast.get_docstring(tree) or ""
check("REUSABLE label", doc.startswith("REUSABLE DECISION PATTERN:"))
check("IS_KIT_EXAMPLE absent", "IS_KIT_EXAMPLE" not in src)
check("PATTERN_TAG = #policy", '"#policy"' in src)
check("QUESTIONS defined", "QUESTIONS" in src)
check("What it does section", "What it does" in doc)
check("Typed questions section", "Typed questions" in doc)
check("Wiring section", "Wiring" in doc)
check("How to reuse section", "reuse" in doc.lower())

print("\n=== eval_cases.jsonl ===")
rows = [json.loads(l) for l in (ROOT / "agent" / "eval_cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
test_rows = [r for r in rows if r.get("split") == "test"]
tune_rows = [r for r in rows if r.get("split") == "tune"]
check(f"Total cases: {len(rows)} (need 24+)", len(rows) >= 24)
check(f"Test split: {len(test_rows)} (need 12+)", len(test_rows) >= 12)
check(f"Tune split: {len(tune_rows)} (need 8+)", len(tune_rows) >= 8)

print("\n=== Syntax checks ===")
for f in ["agent/agent.py", "agent/decision.py", "agent/tools.py"]:
    try:
        ast.parse((ROOT / f).read_text(encoding="utf-8"))
        check(f, True)
    except SyntaxError as e:
        check(f"{f}: {e}", False)

print("\n=== README ===")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
check("AWS User Group Madurai credit", "AWS User Group Madurai" in readme)
check("#policy tag", "#policy" in readme)
check("#strands-decider-2b tag", "#strands-decider-2b" in readme)

print(f"\n{'All checks PASSED' if ok else 'Some checks FAILED'}")
sys.exit(0 if ok else 1)
