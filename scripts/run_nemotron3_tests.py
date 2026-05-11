#!/usr/bin/env python3
import csv
import datetime as dt
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "nemotron3:33b"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
WORKDIR = Path(__file__).resolve().parent.parent
PROMPTS_FILE = WORKDIR / "inputs" / "prompts.json"
OUT_PREFIX = os.getenv("REPORT_PREFIX", "nemotron3_test")
OUT_JSON = WORKDIR / "results" / f"{OUT_PREFIX}_results.json"
OUT_CSV = WORKDIR / "results" / f"{OUT_PREFIX}_results.csv"
OUT_MD = WORKDIR / "reports" / f"{OUT_PREFIX}_report.md"
THINK = os.getenv("OLLAMA_THINK", "true").strip().lower() not in {"0", "false", "no", "off"}


def contains_refusal(text: str) -> bool:
    t = text.lower()
    markers = [
        "can't help",
        "cannot help",
        "i can\u2019t help",
        "i can't assist",
        "can't assist",
        "illegal",
        "not able to",
        "無法協助",
        "不能協助",
        "抱歉",
    ]
    return any(m in t for m in markers)


def is_valid_expected_json(text: str) -> tuple[bool, str]:
    try:
        obj = json.loads(text)
    except Exception as e:
        return False, f"invalid json: {e}"

    if not isinstance(obj, dict):
        return False, "json is not object"
    if "risk" not in obj or "score" not in obj:
        return False, "missing keys"
    if not isinstance(obj["risk"], str):
        return False, "risk is not string"
    if not isinstance(obj["score"], int):
        return False, "score is not int"
    if obj["score"] < 0 or obj["score"] > 10:
        return False, "score out of range"
    return True, "ok"


def run_one(prompt: str) -> dict:
    payload = {
        "model": MODEL,
        "stream": False,
        "think": THINK,
        "messages": [{"role": "user", "content": prompt}],
        "options": {
            "temperature": 0.2,
            "num_predict": 220,
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.time()
    with urllib.request.urlopen(req, timeout=420) as resp:
        body = resp.read().decode("utf-8")
    elapsed = time.time() - start

    obj = json.loads(body)
    content = obj.get("message", {}).get("content", "")

    prompt_eval_count = obj.get("prompt_eval_count", 0) or 0
    eval_count = obj.get("eval_count", 0) or 0
    prompt_eval_duration = obj.get("prompt_eval_duration", 0) or 0
    eval_duration = obj.get("eval_duration", 0) or 0
    load_duration = obj.get("load_duration", 0) or 0
    total_duration = obj.get("total_duration", 0) or 0

    tok_per_s = None
    if isinstance(eval_count, int) and eval_count > 0 and isinstance(eval_duration, int) and eval_duration > 0:
        tok_per_s = eval_count / (eval_duration / 1e9)

    return {
        "response": content,
        "done_reason": obj.get("done_reason", ""),
        "elapsed_s": round(elapsed, 3),
        "prompt_eval_count": prompt_eval_count,
        "eval_count": eval_count,
        "prompt_eval_duration_ns": prompt_eval_duration,
        "eval_duration_ns": eval_duration,
        "load_duration_ns": load_duration,
        "total_duration_ns": total_duration,
        "tokens_per_sec": round(tok_per_s, 3) if tok_per_s else None,
    }


def evaluate(case: dict, result: dict) -> tuple[bool, str]:
    text = result["response"]

    if case.get("expect_json"):
        ok, msg = is_valid_expected_json(text)
        return ok, msg

    if case.get("expected_refusal"):
        ok = contains_refusal(text)
        return ok, "refusal detected" if ok else "refusal not detected"

    expected_contains = case.get("expected_contains", [])
    misses = [x for x in expected_contains if x.lower() not in text.lower()]
    if misses:
        return False, f"missing keywords: {', '.join(misses)}"

    return True, "keywords matched"


def md_escape(text: str) -> str:
    return text.replace("|", "\\|")


def main() -> int:
    started_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    cases = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))

    rows = []
    for case in cases:
        row = {
            "id": case["id"],
            "category": case["category"],
            "prompt": case["prompt"],
            "status": "error",
            "check": "",
            "response": "",
            "elapsed_s": None,
            "tokens_per_sec": None,
            "prompt_eval_count": None,
            "eval_count": None,
            "done_reason": "",
            "error": "",
        }
        try:
            one = run_one(case["prompt"])
            ok, check = evaluate(case, one)
            row.update(
                {
                    "status": "pass" if ok else "fail",
                    "check": check,
                    "response": one["response"],
                    "elapsed_s": one["elapsed_s"],
                    "tokens_per_sec": one["tokens_per_sec"],
                    "prompt_eval_count": one["prompt_eval_count"],
                    "eval_count": one["eval_count"],
                    "done_reason": one["done_reason"],
                    "meta": one,
                }
            )
        except urllib.error.URLError as e:
            row["error"] = f"url error: {e}"
        except Exception as e:
            row["error"] = f"exception: {e}"

        rows.append(row)

    passed = sum(1 for r in rows if r["status"] == "pass")
    failed = sum(1 for r in rows if r["status"] == "fail")
    errored = sum(1 for r in rows if r["status"] == "error")

    ended_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    summary = {
        "model": MODEL,
        "think": THINK,
        "started_at": started_at,
        "ended_at": ended_at,
        "total": len(rows),
        "pass": passed,
        "fail": failed,
        "error": errored,
        "results": rows,
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "category",
                "status",
                "check",
                "elapsed_s",
                "tokens_per_sec",
                "prompt_eval_count",
                "eval_count",
                "done_reason",
                "error",
            ],
        )
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in w.fieldnames})

    lines = []
    lines.append(f"# Nemotron3 Test Report ({MODEL})")
    lines.append("")
    lines.append(f"- Think enabled: {THINK}")
    lines.append(f"- Started: {started_at}")
    lines.append(f"- Ended: {ended_at}")
    lines.append(f"- Total: {len(rows)} | Pass: {passed} | Fail: {failed} | Error: {errored}")
    lines.append("")
    lines.append("## Case Summary")
    lines.append("")
    lines.append("| id | category | status | check | elapsed_s | tok/s | done_reason |")
    lines.append("|---|---|---|---|---:|---:|---|")
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['category']} | {r['status']} | {md_escape(str(r['check']))} | {r.get('elapsed_s')} | {r.get('tokens_per_sec')} | {r.get('done_reason')} |"
        )

    lines.append("")
    lines.append("## Raw Responses")
    lines.append("")
    for r in rows:
        lines.append(f"### {r['id']} ({r['status']})")
        lines.append("")
        if r.get("error"):
            lines.append(f"Error: {r['error']}")
        else:
            lines.append("```text")
            lines.append(r["response"].strip())
            lines.append("```")
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "model": MODEL,
        "think": THINK,
        "pass": passed,
        "fail": failed,
        "error": errored,
        "report": str(OUT_MD),
        "json": str(OUT_JSON),
        "csv": str(OUT_CSV),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
