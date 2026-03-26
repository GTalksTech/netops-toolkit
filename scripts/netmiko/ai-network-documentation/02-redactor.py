# ============================================================
# Script:       02-redactor.py
# Purpose:      Sanitize Cisco IOS device output before sharing or AI ingestion.
#               Credentials are always redacted. Additional categories are opt-in
#               via flags, or enable everything with --redact-all.
# Usage:        python 02-redactor.py <config.cfg>
#               python 02-redactor.py --input-dir output/2026-03-14_123456 --redact-all
#               python 02-redactor.py --input-dir output/2026-03-14_123456 --redact-ips --redact-macs
# Dependencies: re, argparse, pathlib, json (all stdlib -- no pip install needed)
# Author:       G Talks Tech
# Episode:      EP004-L-ai-network-documentation
# GitHub:       github.com/GTalksTech/netops-toolkit
# Notes:        Scoped to Cisco IOS/IOS-XE. Credentials always redacted.
#               All other categories are opt-in via flags.
# ============================================================

import re
import sys
import argparse
from pathlib import Path
import json
from collections import OrderedDict

# ---------------------------------------------------------------------------
# Credential patterns (ALWAYS applied)
# ---------------------------------------------------------------------------

CREDENTIAL_PATTERNS = [
    re.compile(r'(?i)(enable\s+secret(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(enable\s+password(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(username\s+\S+(?:\s+privilege\s+\d+)?\s+secret(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(username\s+\S+(?:\s+privilege\s+\d+)?\s+password(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?im)(^\s+password(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(snmp-server\s+community)\s+(\S+)'),
    re.compile(r'(?i)(tacacs-server\s+key(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(radius-server\s+key(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(ip\s+ospf\s+authentication-key(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(standby\s+\d+\s+authentication)\s+(\S+)'),
    re.compile(r'(?i)(key-string(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(crypto\s+isakmp\s+key(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(neighbor\s+\S+\s+password(?:\s+\d+)?)\s+(\S+)'),
]

# ---------------------------------------------------------------------------
# IPv4 address helpers
# ---------------------------------------------------------------------------

IPV4_RE = re.compile(
    r'(?<![.\d])'
    r'((?:25[0-5]|2[0-4]\d|1?\d{1,2})\.(?:25[0-5]|2[0-4]\d|1?\d{1,2})\.'
    r'(?:25[0-5]|2[0-4]\d|1?\d{1,2})\.(?:25[0-5]|2[0-4]\d|1?\d{1,2}))'
    r'(?![.\d])'
)


def _ip_to_int(ip_str):
    val = 0
    for part in ip_str.split('.'):
        val = (val << 8) | int(part)
    return val


def is_mask(ip_str):
    """Return True if ip_str is a subnet mask or wildcard mask."""
    try:
        val = _ip_to_int(ip_str)
        if val == 0 or val == 0xFFFFFFFF:
            return True
        is_subnet = (val | (val - 1)) == 0xFFFFFFFF
        is_wildcard = (val & (val + 1)) == 0
        return is_subnet or is_wildcard
    except Exception:
        return False


# ---------------------------------------------------------------------------
# MAC address regex
# ---------------------------------------------------------------------------

MAC_CISCO_RE = re.compile(
    r'(?<![0-9a-fA-F\.])'
    r'([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})'
    r'(?![0-9a-fA-F\.])'
)
MAC_COLON_RE = re.compile(
    r'(?<![0-9a-fA-F:])'
    r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:'
    r'[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})'
    r'(?![0-9a-fA-F:])'
)

# ---------------------------------------------------------------------------
# Redaction functions
# ---------------------------------------------------------------------------

def redact_credentials(text):
    """Apply all credential patterns. Returns (redacted_text, match_count)."""
    total = 0
    for pattern in CREDENTIAL_PATTERNS:
        text, n = pattern.subn(lambda m: m.group(1) + ' <REDACTED>', text)
        total += n
    return text, total


def redact_ips(text, existing_map=None, start_counter=1):
    """Replace each unique IPv4 address with <IP_N>. Masks are preserved."""
    ip_map = OrderedDict(existing_map or {})
    counter = [start_counter]

    def replace(match):
        ip = match.group(1)
        if is_mask(ip):
            return match.group(0)
        if ip not in ip_map:
            ip_map[ip] = '<IP_' + str(counter[0]) + '>'
            counter[0] += 1
        return ip_map[ip]

    redacted = IPV4_RE.sub(replace, text)
    return redacted, ip_map


def redact_hostnames(text, existing_map=None, start_counter=1):
    """Detect hostnames from config and replace all occurrences."""
    mapping = dict(existing_map or {})
    counter = [start_counter]

    hostnames = list(dict.fromkeys(re.findall(r'(?im)^hostname\s+(\S+)', text)))
    for h in hostnames:
        if h not in mapping:
            mapping[h] = '<HOSTNAME_' + str(counter[0]) + '>'
            counter[0] += 1

    domain_match = re.search(r'(?im)^ip\s+domain[-\s]name\s+(\S+)', text)
    if domain_match:
        domain = domain_match.group(1)
        if domain not in mapping:
            mapping[domain] = '<DOMAIN_REDACTED>'

    for original in sorted(mapping.keys(), key=len, reverse=True):
        text = text.replace(original, mapping[original])

    return text, mapping

def redact_macs(text, existing_map=None, start_counter=1):
    """Replace MAC addresses with <MAC_N> placeholders."""
    mac_map = OrderedDict(existing_map or {})
    counter = [start_counter]

    def replace_mac(match):
        mac = match.group(1)
        if mac not in mac_map:
            mac_map[mac] = '<MAC_' + str(counter[0]) + '>'
            counter[0] += 1
        return mac_map[mac]

    text = MAC_CISCO_RE.sub(replace_mac, text)
    text = MAC_COLON_RE.sub(replace_mac, text)
    return text, mac_map


def redact_serials(text, existing_map=None, start_counter=1):
    """Replace serial numbers, processor board IDs with <SERIAL_N>."""
    mapping = dict(existing_map or {})
    counter = [start_counter]

    for m in re.finditer(r'Processor board ID\s+(\S+)', text):
        val = m.group(1)
        if val not in mapping:
            mapping[val] = '<SERIAL_' + str(counter[0]) + '>'
            counter[0] += 1

    for m in re.finditer(r'SN:\s*(\S+)', text):
        val = m.group(1)
        if val not in mapping:
            mapping[val] = '<SERIAL_' + str(counter[0]) + '>'
            counter[0] += 1

    for original in sorted(mapping.keys(), key=len, reverse=True):
        text = text.replace(original, mapping[original])

    return text, mapping

def redact_usernames(text, existing_map=None, start_counter=1):
    """Detect usernames from config/logs and replace all occurrences."""
    mapping = dict(existing_map or {})
    counter = [start_counter]

    config_users = re.findall(r'(?im)^username\s+(\S+)', text)
    log_users = re.findall(r'\[user:\s*(\S+?)\]', text)
    by_users = re.findall(r'\bby\s+(\S+)\s+on\s+', text)

    all_users = list(dict.fromkeys(config_users + log_users + by_users))
    for user in all_users:
        if user not in mapping:
            mapping[user] = '<USER_' + str(counter[0]) + '>'
            counter[0] += 1

    for original in sorted(mapping.keys(), key=len, reverse=True):
        text = re.sub(r'\b' + re.escape(original) + r'\b', mapping[original], text)

    return text, mapping


def redact_certificates(text):
    """Strip certificate blocks and hex material. Not mapped (no restore)."""
    text = re.sub(
        r'crypto pki certificate chain\s+\S+.*?quit',
        '<CERTIFICATE_REDACTED>',
        text,
        flags=re.DOTALL
    )
    text = re.sub(
        r'(?m)^\s+certificate (?:self-signed )?\S+\s*\n(?:\s+[0-9A-Fa-f ]+\n)+\s+quit',
        ' <CERTIFICATE_REDACTED>',
        text
    )
    return text

def redact_timestamps(text):
    """Replace timestamps with static placeholder. Not mapped (no restore)."""
    # Cisco log: *Mar 14 10:23:45.123
    text = re.sub(
        r'\*?[A-Z][a-z]{2}\s+\d{1,2}\s+\d{1,2}:\d{2}:\d{2}\.\d+',
        '<TIMESTAMP>',
        text
    )
    # Full datetime: 10:23:45 UTC Fri Mar 14 2026
    text = re.sub(
        r'\d{1,2}:\d{2}:\d{2}\s+\S+\s+\S{3}\s+\S{3}\s+\d{1,2}\s+\d{4}',
        '<TIMESTAMP>',
        text
    )
    # ISO-style from collector: 2026-03-14 12:34:56
    text = re.sub(
        r'\d{4}-\d{2}-\d{2}[_ ]\d{2}:?\d{2}:?\d{2}',
        '<TIMESTAMP>',
        text
    )
    # Uptime line
    text = re.sub(
        r'(uptime is\s+).+',
        r'\1<UPTIME_REDACTED>',
        text
    )
    # Last configuration change at ...
    text = re.sub(
        r'(Last configuration change at\s+).+',
        r'\1<TIMESTAMP>',
        text
    )
    # Configuration last modified by ...
    text = re.sub(
        r'(Configuration last modified by\s+).+',
        r'\1<TIMESTAMP>',
        text
    )
    return text


def redact_versions(text, existing_map=None, start_counter=1):
    """Replace IOS version strings and image filenames with placeholders."""
    mapping = dict(existing_map or {})
    counter = [start_counter]

    for m in re.finditer(r'Version\s+(\d+\.\d+\.\d+[a-zA-Z0-9_.]*)', text):
        ver = m.group(1)
        if ver not in mapping:
            mapping[ver] = '<VERSION_' + str(counter[0]) + '>'
            counter[0] += 1

    for m in re.finditer(r'System image file is "(\S+)"', text):
        img = m.group(1)
        if img not in mapping:
            mapping[img] = '<VERSION_' + str(counter[0]) + '>'
            counter[0] += 1

    for original in sorted(mapping.keys(), key=len, reverse=True):
        text = text.replace(original, mapping[original])

    return text, mapping

def redact_descriptions(text, existing_map=None, start_counter=1):
    """Replace interface description values with <DESCRIPTION_N>."""
    mapping = dict(existing_map or {})
    counter = [start_counter]

    for m in re.finditer(r'(?im)^(\s+description\s+)(.+)$', text):
        desc = m.group(2).strip()
        if desc and desc not in mapping:
            mapping[desc] = '<DESCRIPTION_' + str(counter[0]) + '>'
            counter[0] += 1

    for original in sorted(mapping.keys(), key=len, reverse=True):
        text = text.replace(original, mapping[original])

    return text, mapping


def redact_vlan_names(text, existing_map=None, start_counter=1):
    """Replace VLAN names with <VLAN_NAME_N>."""
    mapping = dict(existing_map or {})
    counter = [start_counter]
    skip_names = {'default', 'fddi-default', 'token-ring-default',
                  'fddinet-default', 'trnet-default'}

    # show vlan brief: "10   Management     active ..."
    for m in re.finditer(
        r'(?m)^(\d{1,4})\s+(.+?)\s{2,}(?:active|suspended|act/unsup|act/lshut)',
        text
    ):
        name = m.group(2).strip()
        if name and name.lower() not in skip_names and name not in mapping:
            mapping[name] = '<VLAN_NAME_' + str(counter[0]) + '>'
            counter[0] += 1

    # Config mode: "name <vlan-name>" under vlan section
    for m in re.finditer(r'(?im)^\s+name\s+(\S+)$', text):
        name = m.group(1)
        if name.lower() not in skip_names and name not in mapping:
            mapping[name] = '<VLAN_NAME_' + str(counter[0]) + '>'
            counter[0] += 1

    # Targeted replacement: only replace in VLAN-specific contexts
    # to avoid hitting protocol field labels like "Management address(es)"
    for original in sorted(mapping.keys(), key=len, reverse=True):
        placeholder = mapping[original]
        # show vlan brief lines: "10   Management     active ..."
        text = re.sub(
            r'(?m)(^\d{1,4}\s+)' + re.escape(original) + r'(\s{2,})',
            lambda m, p=placeholder: m.group(1) + p + m.group(2),
            text
        )
        # Config: "name <vlan-name>" under vlan section
        text = re.sub(
            r'(?im)(^\s+name\s+)' + re.escape(original) + r'$',
            lambda m, p=placeholder: m.group(1) + p,
            text
        )
        # Description references like "Management VLAN" (if not already redacted)
        text = re.sub(
            r'(?im)(^\s+description\s+.*)' + re.escape(original),
            lambda m, o=original, p=placeholder: m.group(0).replace(o, p),
            text
        )

    return text, mapping

# ---------------------------------------------------------------------------
# Counter helper
# ---------------------------------------------------------------------------

def _next_counter(mapping, prefix):
    """Get the next available counter for a placeholder prefix like 'IP_'."""
    if not mapping:
        return 1
    nums = []
    for placeholder in mapping.values():
        m = re.match(r'<' + re.escape(prefix) + r'(\d+)>', placeholder)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1


# ---------------------------------------------------------------------------
# Map persistence
# ---------------------------------------------------------------------------

def save_map(map_path, all_maps):
    """Save all redaction mappings to JSON. Inverts each: placeholder -> original."""
    data = {}
    for category, mapping in all_maps.items():
        if mapping:
            data[category] = {placeholder: original
                              for original, placeholder in mapping.items()}
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return map_path

# ---------------------------------------------------------------------------
# Directory mode
# ---------------------------------------------------------------------------

def process_directory(input_dir, args):
    """Process all device files with a unified redaction map."""
    input_path = Path(input_dir)
    txt_files = sorted(
        list(input_path.glob("*.txt")) + list(input_path.glob("*.cfg")),
        key=lambda p: p.name
    )
    if not txt_files:
        print("[ERROR] No .txt/.cfg files found in: " + str(input_dir), file=sys.stderr)
        sys.exit(1)

    redacted_dir = input_path / "redacted"
    redacted_dir.mkdir(exist_ok=True)

    shared = {
        'ips': OrderedDict(), 'hostnames': {}, 'macs': OrderedDict(),
        'serials': {}, 'usernames': {}, 'versions': {},
        'descriptions': {}, 'vlan_names': {},
    }
    total_creds = 0
    ra = args.redact_all

    print("")
    print("[redact-config] Input dir : " + str(input_path))
    print("  Files found          : " + str(len(txt_files)))

    # Pre-scan all files for hostnames and domains so that neighbor
    # references in CDP/LLDP output are redacted even when the neighbor
    # device is processed in a later file.
    if ra or args.redact_hostnames:
        hn_counter = 1
        for f in txt_files:
            scan_text = f.read_text(encoding="utf-8")
            for h in dict.fromkeys(re.findall(r'(?im)^hostname\s+(\S+)', scan_text)):
                if h not in shared['hostnames']:
                    shared['hostnames'][h] = '<HOSTNAME_' + str(hn_counter) + '>'
                    hn_counter += 1
            dm = re.search(r'(?im)^ip\s+domain[-\s]name\s+(\S+)', scan_text)
            if dm and dm.group(1) not in shared['hostnames']:
                shared['hostnames'][dm.group(1)] = '<DOMAIN_REDACTED>'
        if shared['hostnames']:
            print("  Pre-scan hostnames   : " + str(len(shared['hostnames'])))

    for f in txt_files:
        print("")
        print("  [" + f.name + "]")
        text = f.read_text(encoding="utf-8")

        text, cred_count = redact_credentials(text)
        total_creds += cred_count
        print("    Credentials        : " + str(cred_count))

        if ra or args.redact_certs:
            text = redact_certificates(text)
            print("    Certificates       : stripped")

        if ra or args.redact_descriptions:
            start = _next_counter(shared['descriptions'], 'DESCRIPTION_')
            text, shared['descriptions'] = redact_descriptions(text, shared['descriptions'], start)
            print("    Descriptions       : " + str(len(shared['descriptions'])))

        if ra or args.redact_vlan_names:
            start = _next_counter(shared['vlan_names'], 'VLAN_NAME_')
            text, shared['vlan_names'] = redact_vlan_names(text, shared['vlan_names'], start)
            print("    VLAN names         : " + str(len(shared['vlan_names'])))

        if ra or args.redact_serials:
            start = _next_counter(shared['serials'], 'SERIAL_')
            text, shared['serials'] = redact_serials(text, shared['serials'], start)
            print("    Serials            : " + str(len(shared['serials'])))

        if ra or args.redact_versions:
            start = _next_counter(shared['versions'], 'VERSION_')
            text, shared['versions'] = redact_versions(text, shared['versions'], start)
            print("    Versions           : " + str(len(shared['versions'])))

        if ra or args.redact_hostnames:
            start = _next_counter(shared['hostnames'], 'HOSTNAME_')
            text, shared['hostnames'] = redact_hostnames(text, shared['hostnames'], start)
            print("    Hostnames          : " + str(len(shared['hostnames'])))

        if ra or args.redact_ips:
            start = _next_counter(shared['ips'], 'IP_')
            text, shared['ips'] = redact_ips(text, shared['ips'], start)
            print("    IPs                : " + str(len(shared['ips'])))

        if ra or args.redact_macs:
            start = _next_counter(shared['macs'], 'MAC_')
            text, shared['macs'] = redact_macs(text, shared['macs'], start)
            print("    MACs               : " + str(len(shared['macs'])))

        if ra or args.redact_usernames:
            start = _next_counter(shared['usernames'], 'USER_')
            text, shared['usernames'] = redact_usernames(text, shared['usernames'], start)
            print("    Usernames          : " + str(len(shared['usernames'])))

        if ra or args.redact_timestamps:
            text = redact_timestamps(text)
            print("    Timestamps         : stripped")

        out_path = redacted_dir / f.name
        out_path.write_text(text, encoding="utf-8")
        print("    Saved -> " + f.name)

    map_path = redacted_dir / "map.json"
    save_map(map_path, shared)

    print("")
    print("[redact-config] Summary")
    print("  Credentials          : " + str(total_creds))
    for cat, m in shared.items():
        label = cat.replace('_', ' ').title()
        print("  " + label.ljust(21) + ": " + str(len(m)))
    print("")
    print("[redact-config] Output dir : " + str(redacted_dir))
    print("  Map                  : map.json")
    print("")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Sanitize Cisco IOS device output before sharing or AI ingestion.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='examples:\n  python 02-redactor.py router.cfg\n  python 02-redactor.py --input-dir output/2026-03-14_123456 --redact-all\n  python 02-redactor.py router.cfg --redact-ips --redact-hostnames --redact-macs'
    )
    parser.add_argument('input', nargs='?', help='Path to a single config/output file to redact')
    parser.add_argument('--input-dir', help='Directory of device output files to redact as a batch')
    parser.add_argument('--redact-all', action='store_true', help='Enable all redaction categories')
    parser.add_argument('--redact-ips', action='store_true', help='Replace IPs with <IP_N> placeholders (masks preserved)')
    parser.add_argument('--redact-hostnames', action='store_true', help='Replace hostnames and domain names')
    parser.add_argument('--redact-macs', action='store_true', help='Replace MAC addresses with <MAC_N>')
    parser.add_argument('--redact-serials', action='store_true', help='Replace serial numbers and board IDs with <SERIAL_N>')
    parser.add_argument('--redact-usernames', action='store_true', help='Replace usernames with <USER_N>')
    parser.add_argument('--redact-certs', action='store_true', help='Strip certificate blocks')
    parser.add_argument('--redact-timestamps', action='store_true', help='Replace timestamps with <TIMESTAMP>')
    parser.add_argument('--redact-versions', action='store_true', help='Replace IOS versions and image filenames')
    parser.add_argument('--redact-descriptions', action='store_true', help='Replace interface descriptions with <DESCRIPTION_N>')
    parser.add_argument('--redact-vlan-names', action='store_true', help='Replace VLAN names with <VLAN_NAME_N>')
    parser.add_argument('--output', help='Output file path (single-file mode only)')
    parser.add_argument('--map', help='Existing map JSON to extend (single-file mode only)')
    args = parser.parse_args()

    if args.input_dir:
        process_directory(args.input_dir, args)
        return

    if not args.input:
        parser.error('provide a file path or --input-dir')

    # --- Single-file mode ---
    existing_maps = {
        'ips': OrderedDict(), 'hostnames': {}, 'macs': OrderedDict(),
        'serials': {}, 'usernames': {}, 'versions': {},
        'descriptions': {}, 'vlan_names': {},
    }
    if args.map:
        mp = Path(args.map)
        if not mp.exists():
            print('[ERROR] Map file not found: ' + args.map, file=sys.stderr)
            sys.exit(1)
        with open(mp, 'r', encoding='utf-8') as mf:
            existing = json.load(mf)
        for cat in existing_maps:
            if cat in existing:
                existing_maps[cat] = {v: k for k, v in existing[cat].items()}

    input_path = Path(args.input)
    if not input_path.exists():
        print('[ERROR] File not found: ' + str(input_path), file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding='utf-8')
    ra = args.redact_all

    print('')
    print('[redact-config] Input:  ' + str(input_path))

    text, cred_count = redact_credentials(text)
    print('  Credentials          : ' + str(cred_count))

    if ra or args.redact_certs:
        text = redact_certificates(text)
        print('  Certificates         : stripped')

    if ra or args.redact_descriptions:
        start = _next_counter(existing_maps['descriptions'], 'DESCRIPTION_')
        text, existing_maps['descriptions'] = redact_descriptions(
            text, existing_maps['descriptions'], start)
        print('  Descriptions         : ' + str(len(existing_maps['descriptions'])))

    if ra or args.redact_vlan_names:
        start = _next_counter(existing_maps['vlan_names'], 'VLAN_NAME_')
        text, existing_maps['vlan_names'] = redact_vlan_names(
            text, existing_maps['vlan_names'], start)
        print('  Vlan Names           : ' + str(len(existing_maps['vlan_names'])))

    if ra or args.redact_serials:
        start = _next_counter(existing_maps['serials'], 'SERIAL_')
        text, existing_maps['serials'] = redact_serials(
            text, existing_maps['serials'], start)
        print('  Serials              : ' + str(len(existing_maps['serials'])))

    if ra or args.redact_versions:
        start = _next_counter(existing_maps['versions'], 'VERSION_')
        text, existing_maps['versions'] = redact_versions(
            text, existing_maps['versions'], start)
        print('  Versions             : ' + str(len(existing_maps['versions'])))

    if ra or args.redact_hostnames:
        start = _next_counter(existing_maps['hostnames'], 'HOSTNAME_')
        text, existing_maps['hostnames'] = redact_hostnames(
            text, existing_maps['hostnames'], start)
        print('  Hostnames            : ' + str(len(existing_maps['hostnames'])))

    if ra or args.redact_ips:
        start = _next_counter(existing_maps['ips'], 'IP_')
        text, existing_maps['ips'] = redact_ips(
            text, existing_maps['ips'], start)
        print('  Ips                  : ' + str(len(existing_maps['ips'])))

    if ra or args.redact_macs:
        start = _next_counter(existing_maps['macs'], 'MAC_')
        text, existing_maps['macs'] = redact_macs(
            text, existing_maps['macs'], start)
        print('  Macs                 : ' + str(len(existing_maps['macs'])))

    if ra or args.redact_usernames:
        start = _next_counter(existing_maps['usernames'], 'USER_')
        text, existing_maps['usernames'] = redact_usernames(
            text, existing_maps['usernames'], start)
        print('  Usernames            : ' + str(len(existing_maps['usernames'])))

    if ra or args.redact_timestamps:
        text = redact_timestamps(text)
        print('  Timestamps           : stripped')

    # Write output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_name(
            input_path.stem + '-redacted' + input_path.suffix
        )

    output_path.write_text(text, encoding='utf-8')

    # Save map
    has_mappings = any(existing_maps[cat] for cat in existing_maps)
    if has_mappings:
        map_out = Path(args.map) if args.map else output_path.with_name(
            output_path.stem + '-map.json')
        map_path = save_map(map_out, existing_maps)
        print('  Map saved            : ' + str(map_path))

    print('')
    print('[redact-config] Output: ' + str(output_path))
    print('')


if __name__ == '__main__':
    main()
