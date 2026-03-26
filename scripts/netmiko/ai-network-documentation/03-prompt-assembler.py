# ============================================================
# Script:       03-prompt-assembler.py
# Purpose:      Assemble redacted device output into a paste-ready
#               prompt for Claude or ChatGPT documentation workflows.
# Usage:        python 03-prompt-assembler.py --input-dir output/2026-03-14_123456
#               python 03-prompt-assembler.py --input-dir output/2026-03-14_123456 --output prompt.txt
#               python 03-prompt-assembler.py --input-dir output/2026-03-14_123456 --template custom.txt
# Dependencies: pathlib, argparse (all stdlib -- no pip install needed)
# Author:       G Talks Tech
# Episode:      EP004-L-ai-network-documentation
# GitHub:       github.com/GTalksTech/netops-toolkit
# Notes:        Designed to consume output from 01-collector.py and
#               02-redactor.py. Input dir should contain one .txt file
#               per device named <hostname>.txt.
# ============================================================

import argparse
import sys
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# NL is used instead of the escape sequence to avoid tooling issues.
# ---------------------------------------------------------------------------
NL = chr(10)

# ---------------------------------------------------------------------------
# Default prompt template
# ---------------------------------------------------------------------------

PROMPT_HEADER = (
    "You are a network documentation engineer producing an operational runbook "
    "for a senior network engineer. This runbook must be immediately usable "
    "during incidents and change planning -- not a training document." + NL + NL +
    "CRITICAL: The device output contains sanitized placeholder tokens. "
    "You MUST copy every placeholder into your output exactly as written -- same "
    "angle brackets, same capitalization, same underscore format. "
    "Do NOT expand, paraphrase, resolve, or reformat them in any way. "
    "Treat them as opaque string literals." + NL + NL +
    "Placeholder types you may encounter:" + NL +
    "- <IP_1>, <IP_2> ... (IP addresses)" + NL +
    "- <HOSTNAME_1>, <HOSTNAME_2> ... (device hostnames)" + NL +
    "- <DOMAIN_REDACTED> (domain name)" + NL +
    "- <MAC_1>, <MAC_2> ... (MAC addresses)" + NL +
    "- <SERIAL_1>, <SERIAL_2> ... (serial numbers and board IDs)" + NL +
    "- <USER_1>, <USER_2> ... (usernames)" + NL +
    "- <VERSION_1>, <VERSION_2> ... (IOS versions and image filenames)" + NL +
    "- <DESCRIPTION_1>, <DESCRIPTION_2> ... (interface descriptions)" + NL +
    "- <VLAN_NAME_1>, <VLAN_NAME_2> ... (VLAN names)" + NL +
    "- <CERTIFICATE_REDACTED> (stripped certificate blocks)" + NL +
    "- <TIMESTAMP>, <UPTIME_REDACTED> (timestamps and uptime)" + NL +
    "- <REDACTED> (credentials)" + NL + NL +
    "Generate a Markdown runbook with these sections in this order:" + NL +
    "1. ## Topology Overview -- prose paragraph + device role table "
    "(Device | Role | Connected To)" + NL +
    "2. ## Device Inventory -- table: Hostname | Model | IOS Version | Serial" + NL +
    "3. ## IP Addressing -- table per device: Interface | IP/Prefix | Description | Status" + NL +
    "4. ## Routing Summary -- one subsection per device: protocol, neighbors table, "
    "advertised networks, passive interfaces" + NL +
    "5. ## Layer 2 Summary -- only for devices with L2 output: VLAN table, "
    "trunk table (Port | Allowed VLANs | Native VLAN), STP root per VLAN" + NL +
    "6. ## Management Services -- NTP source/server, SSH version, syslog targets, "
    "AAA method if present. Table format." + NL +
    "7. ## Findings and Flags -- numbered list. Flag mismatches, missing configs, "
    "suboptimal settings based on what is visible in the output. "
    "If values are redacted, note what could not be assessed. "
    "If nothing noteworthy, write 'None identified.'" + NL + NL +
    "Formatting rules:" + NL +
    "- Use Markdown tables for all structured data. No bullet lists where a table fits." + NL +
    "- Use H3 (###) for per-device subsections within any H2 section." + NL +
    "- Use only values from the device output. No assumptions or invented values." + NL +
    "- If a value is not present in the output, write 'Not found in output'." + NL +
    "- Place placeholder tokens directly into table cells and prose. "
    "They will be restored to real values after generation." + NL + NL +
    "--- DEVICE OUTPUT START ---" + NL
)
PROMPT_FOOTER = (
    NL + "--- DEVICE OUTPUT END ---" + NL + NL +
    "Generate the runbook now." + NL
)

# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def load_template(template_path):
    """Load a custom prompt header from a .txt file."""
    p = Path(template_path)
    if not p.exists():
        print("[ERROR] Template not found: " + template_path, file=sys.stderr)
        sys.exit(1)
    return p.read_text(encoding="utf-8").rstrip() + NL + NL + "--- DEVICE OUTPUT START ---" + NL


def assemble_prompt(input_dir, header, footer):
    """Read all .txt device files and assemble the prompt.

    Files are processed in sorted order (alphabetical by filename).
    Each device file is wrapped in a clearly labeled block so the AI
    knows where one device ends and the next begins.

    Returns (prompt_text, list_of_files).
    """
    txt_files = sorted(
        list(Path(input_dir).glob("*.txt")) + list(Path(input_dir).glob("*.cfg")),
        key=lambda p: p.name
    )
    if not txt_files:
        print("[ERROR] No .txt files found in: " + str(input_dir), file=sys.stderr)
        sys.exit(1)

    div = "=" * 60
    sections = [header]

    for idx, f in enumerate(txt_files, 1):
        content = f.read_text(encoding="utf-8").strip()
        sections.append(NL + NL + "[[ DEVICE " + str(idx) + " ]]")
        sections.append(NL + div)
        sections.append(NL + content)
        sections.append(NL)

    sections.append(footer)
    return "".join(sections), txt_files

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Assemble redacted device output into a paste-ready AI prompt.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='examples:\n  python 03-prompt-assembler.py --input-dir output/2026-03-14_123456\n  python 03-prompt-assembler.py --input-dir output/2026-03-14_123456 --output prompt.txt\n  python 03-prompt-assembler.py --input-dir output/2026-03-14_123456 --template custom.txt'
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing .txt device output files (from 01-collector.py)"
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: <input-dir>/prompt-<timestamp>.txt)"
    )
    parser.add_argument(
        "--template",
        help="Path to a custom prompt header .txt file (replaces the built-in instructions)"
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print("[ERROR] Directory not found: " + str(input_dir), file=sys.stderr)
        sys.exit(1)

    header = load_template(args.template) if args.template else PROMPT_HEADER
    prompt, files = assemble_prompt(input_dir, header, PROMPT_FOOTER)

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        output_path = input_dir.parent / ("prompt-" + timestamp + ".txt")

    output_path.write_text(prompt, encoding="utf-8")

    char_count = len(prompt)
    word_count = len(prompt.split())
    token_est = int(word_count * 1.3)

    print("")
    print("[prompt-assembler] Input dir : " + str(input_dir))
    print("  Devices assembled  : " + str(len(files)))
    for f in files:
        print("    - " + f.name)
    print("  Prompt size        : " + f"{char_count:,} chars / ~{word_count:,} words / ~{token_est:,} tokens")
    print("")
    print("[prompt-assembler] Output    : " + str(output_path))
    print("")
    print("  Next steps:")
    print("    1. Paste the contents of that file into Claude or ChatGPT.")
    print("    2. Save the AI response to a .md file.")
    print("    3. Run 04-restore.py to swap placeholders back to real values.")
    print("")


if __name__ == "__main__":
    main()

