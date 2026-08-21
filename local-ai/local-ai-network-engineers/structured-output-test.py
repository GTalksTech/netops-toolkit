# ============================================================
# Script:       structured-output-test.py
# Purpose:      Test Ollama structured outputs (format=<JSON schema>) +
#               Pydantic validation on a real config extraction, then probe
#               the two claimed llama.cpp grammar bugs (nested $ref
#               fallback; thinking-mode grammar bypass).
# Usage:        python structured-output-test.py [--model qwen3.6:35b]
# Dependencies: pydantic (pip install -r requirements.txt), stdlib urllib/json
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
import sys
import urllib.request

from pydantic import BaseModel, ValidationError

OLLAMA = "http://127.0.0.1:11434/api/generate"

STRICT = {"temperature": 0.0, "top_p": 0.1, "top_k": 10, "num_ctx": 32768}


class Interface(BaseModel):
    name: str
    ip: str
    mask: str
    description: str
    status: str


class ExtractResult(BaseModel):
    interfaces: list[Interface]


# Plain schema (test 1) -- mirrors the Pydantic model, no $ref indirection
PLAIN_SCHEMA = {
    "type": "object",
    "properties": {
        "interfaces": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "ip": {"type": "string"},
                    "mask": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string"},
                },
                "required": ["name", "ip", "mask", "description", "status"],
            },
        }
    },
    "required": ["interfaces"],
}

# Nested-$ref schema (test 2) -- semantically identical, but via $defs/$ref,
# which the digest claims triggers a SILENT fallback to free text.
REF_SCHEMA = {
    "$defs": {
        "iface": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "ip": {"type": "string"},
                "mask": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string"},
            },
            "required": ["name", "ip", "mask", "description", "status"],
        }
    },
    "type": "object",
    "properties": {
        "interfaces": {"type": "array", "items": {"$ref": "#/$defs/iface"}}
    },
    "required": ["interfaces"],
}

PROMPT = (
    "Extract every interface that has an IPv4 address from this running-config, "
    "with name, ip, mask, description, and admin status. Config:\n\n"
)


def ask(model, prompt, fmt=None, think=None):
    body = {"model": model, "prompt": prompt, "stream": False, "options": STRICT}
    if fmt is not None:
        body["format"] = fmt
    if think is not None:
        body["think"] = think
    req = urllib.request.Request(
        OLLAMA,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def validate(label, raw_text):
    print(f"\n--- {label}")
    print(f"    raw head: {raw_text[:120]!r}")
    try:
        parsed = ExtractResult.model_validate_json(raw_text)
    except (ValidationError, ValueError) as e:
        print(f"    RESULT: FAILED validation -- {type(e).__name__}: {str(e)[:200]}")
        return None
    names = {i.name: i.ip for i in parsed.interfaces}
    print(f"    RESULT: VALID JSON, {len(parsed.interfaces)} interfaces: {names}")
    expected = {
        "Loopback0": "10.0.0.1",
        "Ethernet0/0": "192.168.1.250",
        "Ethernet0/1": "10.0.12.2",
    }
    print(f"    ground truth match: {'YES' if names == expected else 'NO -- diff: ' + str(set(names.items()) ^ set(expected.items()))}")
    return parsed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3.6:35b")
    ap.add_argument("--config", default="core-rtr-01.cfg")
    args = ap.parse_args()

    config = (pathlib.Path(__file__).parent / args.config).read_text()
    prompt = PROMPT + config

    # Test 1: plain schema, thinking default
    r1 = ask(args.model, prompt, fmt=PLAIN_SCHEMA)
    validate("T1 plain schema (think default)", r1.get("response", ""))

    # Test 2: nested-$ref schema -- claimed silent fallback
    r2 = ask(args.model, prompt, fmt=REF_SCHEMA)
    validate("T2 nested-$ref schema (bug probe 1)", r2.get("response", ""))

    # Test 3: plain schema with thinking explicitly ON -- claimed grammar bypass
    r3 = ask(args.model, prompt, fmt=PLAIN_SCHEMA, think=True)
    validate("T3 plain schema + think=true (bug probe 2)", r3.get("response", ""))

    print("\nDone. Only claims that reproduced here go on camera.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
