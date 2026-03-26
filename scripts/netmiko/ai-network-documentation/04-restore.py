# ============================================================
# Script:       04-restore.py
# Purpose:      Restore redacted values into AI-generated
#               documentation by reversing the redaction map.
# Usage:        python 04-restore.py <doc.md> <map.json>
#               python 04-restore.py <doc.md> <map.json> --output restored.md
# Dependencies: json, argparse, pathlib (all stdlib -- no pip install needed)
# Author:       G Talks Tech
# Episode:      EP004-L-ai-network-documentation
# GitHub:       github.com/GTalksTech/netops-toolkit
# Notes:        Designed to work with map.json produced by 02-redactor.py.
#               Run after saving AI-generated output to a file.
# ============================================================

import json
import sys
import argparse
from pathlib import Path


def load_map(map_path):
    """Load and merge all category dicts from the JSON map file.

    Returns a single dict of {placeholder: original_value}.
    """
    with open(map_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    combined = {}
    for category in data.values():
        combined.update(category)
    return combined


def restore(text, mapping):
    """Replace placeholders with real values.

    Processes longest placeholders first to prevent partial matches
    (e.g. <IP_10> must be replaced before <IP_1>).

    Returns (restored_text, count_of_placeholders_found).
    """
    found = 0
    for placeholder in sorted(mapping.keys(), key=len, reverse=True):
        original = mapping[placeholder]
        if placeholder in text:
            text = text.replace(placeholder, original)
            found += 1
    return text, found

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Restore real values into AI-generated docs using the redaction map.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:" + chr(10) +
            "  python 04-restore.py runbook.md lab-configurations-redacted-map.json" + chr(10) +
            "  python 04-restore.py runbook.md map.json --output runbook-final.md"
        )
    )
    parser.add_argument("doc",  help="Path to the AI-generated document")
    parser.add_argument("map",  help="Path to the JSON map file from 02-redactor.py")
    parser.add_argument(
        "--output",
        help="Output file path (default: <doc-stem>-restored<ext>)"
    )
    args = parser.parse_args()

    doc_path = Path(args.doc)
    map_path = Path(args.map)

    if not doc_path.exists():
        print("[ERROR] Document not found: " + str(doc_path), file=sys.stderr)
        sys.exit(1)
    if not map_path.exists():
        print("[ERROR] Map file not found: " + str(map_path), file=sys.stderr)
        sys.exit(1)

    mapping = load_map(map_path)
    if not mapping:
        print("[ERROR] Map file is empty -- nothing to restore.", file=sys.stderr)
        sys.exit(1)

    text = doc_path.read_text(encoding="utf-8")
    text, found = restore(text, mapping)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = doc_path.with_name(doc_path.stem + "-restored" + doc_path.suffix)

    output_path.write_text(text, encoding="utf-8")

    print("")
    print("[restore] Input doc  : " + str(doc_path))
    print("[restore] Map file   : " + str(map_path))
    print("  Entries in map     : " + str(len(mapping)))
    print("  Placeholders found : " + str(found) + " of " + str(len(mapping)))
    print("")
    print("[restore] Output     : " + str(output_path))
    print("")


if __name__ == "__main__":
    main()
