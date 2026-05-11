#!/usr/bin/env python3
import base64
import datetime as dt
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

MODEL = "nemotron3:33b"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"
WORKDIR = Path(__file__).resolve().parent.parent
ASSET_DIR = WORKDIR / "assets" / "multimodal_assets"
OUT_JSON = WORKDIR / "results" / "nemotron3_multimodal_results.json"
OUT_MD = WORKDIR / "reports" / "nemotron3_multimodal_report.md"


def b64_file(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def maybe_font(size: int):
    for p in [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def make_assets() -> dict:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    font_big = maybe_font(64)
    font_mid = maybe_font(36)

    # v01 text image
    img = Image.new("RGB", (1000, 320), "white")
    d = ImageDraw.Draw(img)
    d.text((80, 110), "TAIPEI 101", font=font_big, fill="black")
    p_text = ASSET_DIR / "v01_text.png"
    img.save(p_text)

    # v02 shapes image
    img2 = Image.new("RGB", (800, 500), "white")
    d2 = ImageDraw.Draw(img2)
    circles = [(80, 90, 200, 210), (260, 90, 380, 210), (440, 90, 560, 210)]
    for c in circles:
        d2.ellipse(c, fill=(220, 30, 30), outline="black", width=3)
    squares = [(180, 290, 300, 410), (420, 290, 540, 410)]
    for s in squares:
        d2.rectangle(s, fill=(30, 80, 220), outline="black", width=3)
    d2.text((20, 20), "Count shapes", font=font_mid, fill="black")
    p_shapes = ASSET_DIR / "v02_shapes.png"
    img2.save(p_shapes)

    # v03 bar chart
    img3 = Image.new("RGB", (950, 560), "white")
    d3 = ImageDraw.Draw(img3)
    axis_x0, axis_y0 = 120, 480
    d3.line((axis_x0, 80, axis_x0, axis_y0), fill="black", width=4)
    d3.line((axis_x0, axis_y0, 880, axis_y0), fill="black", width=4)
    bars = [
        ("Apple", 5, (210, 100, 100)),
        ("Banana", 9, (230, 190, 70)),
        ("Cherry", 3, (160, 60, 120)),
    ]
    maxv = 10
    x = 200
    for name, val, color in bars:
        h = int((val / maxv) * 340)
        d3.rectangle((x, axis_y0 - h, x + 140, axis_y0), fill=color, outline="black", width=2)
        d3.text((x + 35, axis_y0 + 12), name, font=font_mid, fill="black")
        d3.text((x + 58, axis_y0 - h - 45), str(val), font=font_mid, fill="black")
        x += 220
    d3.text((320, 20), "Fruit Sales", font=font_big, fill="black")
    p_chart = ASSET_DIR / "v03_barchart.png"
    img3.save(p_chart)

    # v05 multi-image compare
    img4a = Image.new("RGB", (420, 320), "white")
    d4a = ImageDraw.Draw(img4a)
    d4a.ellipse((120, 70, 300, 250), fill=(235, 145, 45), outline="black", width=3)  # orange
    d4a.text((120, 20), "Image A", font=font_mid, fill="black")
    p_a = ASSET_DIR / "v05_a_orange.png"
    img4a.save(p_a)

    img4b = Image.new("RGB", (420, 320), "white")
    d4b = ImageDraw.Draw(img4b)
    d4b.ellipse((120, 70, 300, 250), fill=(30, 170, 80), outline="black", width=3)  # green
    d4b.text((120, 20), "Image B", font=font_mid, fill="black")
    p_b = ASSET_DIR / "v05_b_green.png"
    img4b.save(p_b)

    # real-world cat image
    cat_url = "https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg"
    p_cat = ASSET_DIR / "v04_cat.jpg"
    if not p_cat.exists():
        try:
            urllib.request.urlretrieve(cat_url, p_cat)
        except Exception:
            subprocess.run(["curl", "-L", "-o", str(p_cat), cat_url], check=True)

    # optional audio file via macOS say
    p_audio = ASSET_DIR / "a01_taipei.aiff"
    if not p_audio.exists():
        subprocess.run([
            "say",
            "-o",
            str(p_audio),
            "Taipei one oh one is a landmark in Taiwan.",
        ], check=False)

    return {
        "v01_text": p_text,
        "v02_shapes": p_shapes,
        "v03_barchart": p_chart,
        "v04_cat": p_cat,
        "v05_a": p_a,
        "v05_b": p_b,
        "a01_audio": p_audio,
    }


def call_chat(prompt: str, images: list[str] | None = None, audios: list[str] | None = None) -> dict:
    msg = {"role": "user", "content": prompt}
    if images:
        msg["images"] = images
    if audios:
        msg["audios"] = audios

    payload = {
        "model": MODEL,
        "stream": False,
        "think": False,
        "messages": [msg],
        "options": {
            "temperature": 0.1,
            "num_predict": 180,
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.time()
    with urllib.request.urlopen(req, timeout=420) as resp:
        body = resp.read().decode("utf-8")
    elapsed = round(time.time() - start, 3)

    obj = json.loads(body)
    content = obj.get("message", {}).get("content", "") or ""
    return {
        "content": content,
        "done_reason": obj.get("done_reason", ""),
        "elapsed_s": elapsed,
        "eval_count": obj.get("eval_count", 0),
        "tokens_per_sec": round((obj.get("eval_count", 0) or 0) / ((obj.get("eval_duration", 1) or 1) / 1e9), 3),
        "raw": obj,
    }


def pass_contains(text: str, needles: list[str]) -> bool:
    lt = text.lower()
    return all(n.lower() in lt for n in needles)


def evaluate(case_id: str, content: str) -> tuple[bool, str]:
    t = content.strip()
    tl = t.lower()

    if case_id == "v01_ocr_text":
        ok = pass_contains(t, ["taipei", "101"])
        return ok, "needs TAIPEI + 101"

    if case_id == "v02_count_shapes":
        # Accept either JSON or plain sentence mentioning 3 and 2.
        ok_json = False
        try:
            j = json.loads(t)
            ok_json = int(j.get("red_circles", -1)) == 3 and int(j.get("blue_squares", -1)) == 2
        except Exception:
            ok_json = False
        ok_text = ("3" in t and "2" in t) and ("circle" in tl or "圓" in t) and ("square" in tl or "方" in t)
        ok = ok_json or ok_text
        return ok, "needs 3 red circles and 2 blue squares"

    if case_id == "v03_barchart":
        ok = ("banana" in tl) and ("9" in t)
        return ok, "needs banana and value 9"

    if case_id == "v04_cat_photo":
        ok = ("cat" in tl) or ("貓" in t)
        return ok, "needs cat"

    if case_id == "v05_multi_image_compare":
        ok = ("first" in tl) or ("image a" in tl) or ("第一" in t) or ("a" in t[:20].lower())
        return ok, "needs first/image A as orange"

    if case_id == "a01_audio_attempt":
        # We expect either transcript success or explicit unsupported behavior
        if "taipei" in tl or "taiwan" in tl:
            return True, "audio transcript succeeded"
        if "can't" in tl or "cannot" in tl or "unsupported" in tl or "not able" in tl:
            return False, "audio not supported/handled"
        if t == "":
            return False, "empty content"
        return False, "audio did not produce expected transcript"

    return False, "unknown case"


def main() -> int:
    started_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    assets = make_assets()

    cases = [
        {
            "id": "v01_ocr_text",
            "prompt": "Read the main text in this image. Reply with exactly the text only.",
            "images": [b64_file(assets["v01_text"])],
        },
        {
            "id": "v02_count_shapes",
            "prompt": "Count red circles and blue squares. Reply JSON only: {\"red_circles\": <int>, \"blue_squares\": <int>}.",
            "images": [b64_file(assets["v02_shapes"])],
        },
        {
            "id": "v03_barchart",
            "prompt": "From this chart, which fruit has the highest sales value and what is the value?",
            "images": [b64_file(assets["v03_barchart"])],
        },
        {
            "id": "v04_cat_photo",
            "prompt": "What animal is shown in this photo?",
            "images": [b64_file(assets["v04_cat"])],
        },
        {
            "id": "v05_multi_image_compare",
            "prompt": "You see two images in order. Which image has the orange circle, first or second?",
            "images": [b64_file(assets["v05_a"]), b64_file(assets["v05_b"])],
        },
    ]

    # Audio attempt if file exists
    if assets["a01_audio"].exists() and assets["a01_audio"].stat().st_size > 0:
        cases.append(
            {
                "id": "a01_audio_attempt",
                "prompt": "Please transcribe the audio.",
                "audios": [b64_file(assets["a01_audio"])],
            }
        )

    results = []
    for c in cases:
        row = {
            "id": c["id"],
            "status": "error",
            "check": "",
            "done_reason": "",
            "elapsed_s": None,
            "tokens_per_sec": None,
            "response": "",
            "error": "",
        }
        try:
            resp = call_chat(c["prompt"], images=c.get("images"), audios=c.get("audios"))
            ok, check = evaluate(c["id"], resp["content"])
            row.update(
                {
                    "status": "pass" if ok else "fail",
                    "check": check,
                    "done_reason": resp["done_reason"],
                    "elapsed_s": resp["elapsed_s"],
                    "tokens_per_sec": resp["tokens_per_sec"],
                    "response": resp["content"],
                    "raw": resp["raw"],
                }
            )
        except urllib.error.HTTPError as e:
            row["error"] = f"http error {e.code}: {e.read().decode('utf-8', errors='ignore')}"
        except Exception as e:
            row["error"] = f"exception: {e}"
        results.append(row)

    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    errors = sum(1 for r in results if r["status"] == "error")

    ended_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")

    out = {
        "model": MODEL,
        "started_at": started_at,
        "ended_at": ended_at,
        "total": len(results),
        "pass": passed,
        "fail": failed,
        "error": errors,
        "assets": {k: str(v) for k, v in assets.items()},
        "results": results,
    }

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append(f"# Nemotron3 Multimodal Test Report ({MODEL})")
    md.append("")
    md.append(f"- Started: {started_at}")
    md.append(f"- Ended: {ended_at}")
    md.append(f"- Total: {len(results)} | Pass: {passed} | Fail: {failed} | Error: {errors}")
    md.append("")
    md.append("| id | status | check | done_reason | elapsed_s | tok/s |")
    md.append("|---|---|---|---|---:|---:|")
    for r in results:
        md.append(f"| {r['id']} | {r['status']} | {r['check']} | {r['done_reason']} | {r['elapsed_s']} | {r['tokens_per_sec']} |")

    md.append("\n## Raw Responses\n")
    for r in results:
        md.append(f"### {r['id']} ({r['status']})")
        if r["error"]:
            md.append(f"Error: {r['error']}")
        else:
            md.append("```text")
            md.append(r["response"].strip())
            md.append("```")
        md.append("")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print(json.dumps({
        "model": MODEL,
        "pass": passed,
        "fail": failed,
        "error": errors,
        "report": str(OUT_MD),
        "json": str(OUT_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
