# ============================================================
# Script:       sampling-ab-test.py
# Purpose:      A/B test extraction sampling settings (default vs strict)
#               against real lab configs, machine-scoring hallucinated and
#               missed IPs per run.
# Usage:        python sampling-ab-test.py [--config core-rtr-01.cfg]
# Dependencies: stdlib only (urllib, json, re) -- needs Ollama running
# Author:       G Talks Tech
# GitHub:       github.com/GTalksTech/netops-toolkit
# Notes:        Public by design. All IPs are REAL lab IPs (RFC1918) --
#               the lab is meant to be replicated, never use placeholders.
#               Never hardcode credentials. Use getpass for passwords;
#               never accept a --password argument.
# ============================================================

import argparse
import json
import pathlib
import re
import sys
import urllib.request

OLLAMA = "http://127.0.0.1:11434/api/generate"

MODELS = ["qwen3.6:35b", "laguna-xs-2.1"]
RUNS_PER_PROFILE = 2

PROFILES = {
    "default": {},  # whatever the model card ships
    "strict": {
        "temperature": 0.0,
        "top_p": 0.1,
        "top_k": 10,
        "repeat_penalty": 1.15,
    },
}

# The three interface IPs that MUST appear (ground truth for core-rtr-01)
REQUIRED_IPS = {"10.0.0.1", "192.168.1.250", "10.0.12.2"}

IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

PROMPT = (
    "Extract every interface that has an IPv4 address from this running-config. "
    "For each, report: interface name, IP address, subnet mask. Use ONLY "
    "information present in the config. Config:\n\n"
)


def ask(model: str, prompt: str, options: dict) -> dict:
    opts = {"num_ctx": 32768}
    opts.update(options)
    body = json.dumps(
        {"model": model, "prompt": prompt, "stream": False, "options": opts}
    ).encode()
    req = urllib.request.Request(
        OLLAMA, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def score(response_text: str, grounded_ips: set) -> dict:
    found = set(IP_RE.findall(response_text))
    return {
        "fabricated": sorted(found - grounded_ips),
        "missed": sorted(REQUIRED_IPS - found),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="core-rtr-01.cfg")
    args = ap.parse_args()

    cfg_path = pathlib.Path(__file__).parent / args.config
    config = cfg_path.read_text()
    # Every IP-shaped string in the config is "grounded"; anything else
    # in a response was invented by the model.
    grounded = set(IP_RE.findall(config))

    results = []
    for model in MODELS:
        for pname, popts in PROFILES.items():
            for run in range(1, RUNS_PER_PROFILE + 1):
                print(f"--- {model} | {pname} | run {run} ...", flush=True)
                resp = ask(model, PROMPT + config, popts)
                text = resp.get("response", "")
                s = score(text, grounded)
                tokps = (
                    resp["eval_count"] / (resp["eval_duration"] / 1e9)
                    if resp.get("eval_duration")
                    else None
                )
                row = {
                    "model": model,
                    "profile": pname,
                    "run": run,
                    "fabricated": s["fabricated"],
                    "missed": s["missed"],
                    "eval_tokens": resp.get("eval_count"),
                    "tok_per_s": round(tokps, 2) if tokps else None,
                }
                results.append(row)
                print(
                    f"    fabricated={row['fabricated'] or 'NONE'} "
                    f"missed={row['missed'] or 'NONE'} "
                    f"tokens={row['eval_tokens']} @ {row['tok_per_s']} tok/s"
                )

    out = pathlib.Path(__file__).parent / "sampling-ab-results.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nSaved: {out}")

    print("\n=== SUMMARY (fabricated / missed per run) ===")
    for r in results:
        flag = "CLEAN" if not r["fabricated"] and not r["missed"] else "DIRTY"
        print(
            f"{r['model']:<16} {r['profile']:<8} run{r['run']}  "
            f"fab={len(r['fabricated'])} miss={len(r['missed'])}  {flag}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
