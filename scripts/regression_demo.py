import json
import subprocess
from pathlib import Path


def run_case(case_id: str):
    cmd = ["python", "-m", "autopipeline", "run", "--case", case_id, "--llm-provider", "mock"]
    subprocess.check_call(cmd)
    eval_path = Path("outputs") / case_id / "eval.json"
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    assert data.get("overall_status") == "PASS", f"{case_id} not PASS"
    assert "validators" in data and "failures_flat" in data, "missing new fields"
    print(f"[ok] {case_id}")


if __name__ == "__main__":
    for case in ["DEMO-MONITORING", "DEMO-SMARTHOME"]:
        run_case(case)
    print("All demo regressions passed.")
