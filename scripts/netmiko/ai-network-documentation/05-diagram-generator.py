# ============================================================
# Script:       05-diagram-generator.py
# Purpose:      Generate a draw.io network diagram from collected show output
# Usage:        python 05-diagram-generator.py --input-dir output/<timestamp>/
# Dependencies: none (standard library only)
# Author:       G Talks Tech
# Episode:      EP004-L-ai-network-documentation
# GitHub:       github.com/GTalksTech/netops-toolkit
# Notes:        Runs entirely offline. No data leaves your machine.
#               Uses CDP neighbor data and show ip interface brief
#               to build topology. Open the .drawio file in draw.io
#               and use Arrange > Layout if you want to adjust placement.
# ============================================================

import argparse
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom


# -----------------------------------------------------------------------
# Styles
# -----------------------------------------------------------------------
ROUTER_STYLE = (
    "verticalLabelPosition=bottom;html=1;verticalAlign=top;"
    "aspect=fixed;align=center;pointerEvents=1;"
    "shape=mxgraph.cisco19.rect;prIcon=router;"
    "fillColor=#FAFAFA;strokeColor=#005073;"
)

SWITCH_STYLE = (
    "verticalLabelPosition=bottom;html=1;verticalAlign=top;"
    "aspect=fixed;align=center;pointerEvents=1;"
    "shape=mxgraph.cisco19.rect;prIcon=l2_switch;"
    "fillColor=#FAFAFA;strokeColor=#005073;"
)

EDGE_STYLE = (
    "endFill=0;endArrow=none;html=1;rounded=0;"
    "strokeColor=#005073;fontSize=10;"
)

# -----------------------------------------------------------------------
# Layout constants
# -----------------------------------------------------------------------
NODE_W = 50
NODE_H = 50
H_SPACING = 200       # horizontal gap between devices in the same tier
V_SPACING = 180       # vertical gap between tiers
LEFT_MARGIN = 100
TOP_MARGIN = 80

# Tier order: edge at top, core in middle, access at bottom
TIER_ORDER = {"edge": 0, "core": 1, "access": 2, "other": 3}


# -----------------------------------------------------------------------
# Parsing helpers
# -----------------------------------------------------------------------
def extract_sections(text):
    """Split a collector output file into {command: output} sections."""
    parts = re.split(r"={40,}\nCOMMAND: (.+)\n={40,}\n", text)
    sections = {}
    # parts[0] is the header, then pairs of (command, output)
    for i in range(1, len(parts) - 1, 2):
        sections[parts[i].strip()] = parts[i + 1]
    return sections


def parse_device_header(text):
    """Extract device name and role hint from the collector header."""
    name_match = re.search(r"^DEVICE:\s+(.+)$", text, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else "unknown"
    return name


def detect_role(name, sections):
    """Detect device role from hostname pattern and available commands."""
    lower = name.lower()
    if "sw" in lower or "switch" in lower:
        return "switch"
    if "fw" in lower or "firewall" in lower:
        return "firewall"
    # Check if switch-specific commands are present
    if "show vlan brief" in sections:
        return "switch"
    return "router"


def classify_tier(name):
    """Assign a layout tier based on hostname prefix."""
    lower = name.lower()
    if lower.startswith("edge"):
        return "edge"
    if lower.startswith("core"):
        return "core"
    if lower.startswith("access") or lower.startswith("dist"):
        return "access"
    return "other"


def parse_ip_interfaces(section_text):
    """Parse show ip interface brief into {interface: ip}."""
    interfaces = {}
    for line in section_text.splitlines():
        m = re.match(
            r"^(\S+)\s+(\d+\.\d+\.\d+\.\d+)\s+YES",
            line,
        )
        if m:
            interfaces[m.group(1)] = m.group(2)
    return interfaces


def normalize_intf(raw):
    """Normalize interface names: Et0/0 -> Ethernet0/0, Gi0/1 -> GigabitEthernet0/1, etc."""
    raw = raw.strip()
    abbrevs = [
        (r"^Et(\d)", r"Ethernet\1"),
        (r"^Eth(\d)", r"Ethernet\1"),
        (r"^Gi(\d)", r"GigabitEthernet\1"),
        (r"^Fa(\d)", r"FastEthernet\1"),
        (r"^Te(\d)", r"TenGigabitEthernet\1"),
        (r"^Lo(\d)", r"Loopback\1"),
    ]
    for pattern, replacement in abbrevs:
        raw = re.sub(pattern, replacement, raw)
    return raw


def shorten_intf(name):
    """Shorten interface name for edge labels: Ethernet0/0 -> E0/0."""
    name = re.sub(r"^Ethernet", "E", name)
    name = re.sub(r"^GigabitEthernet", "Gi", name)
    name = re.sub(r"^FastEthernet", "Fa", name)
    name = re.sub(r"^TenGigabitEthernet", "Te", name)
    return name


def parse_cdp_neighbors(section_text):
    """Parse show cdp neighbors detail into a list of neighbor dicts."""
    neighbors = []
    entries = re.split(r"^-{10,}", section_text, flags=re.MULTILINE)
    for entry in entries:
        dev_match = re.search(r"Device ID:\s*(\S+)", entry)
        local_match = re.search(
            r"Interface:\s*(\S+),\s*Port ID \(outgoing port\):\s*(\S+)", entry
        )
        if dev_match and local_match:
            remote_name = dev_match.group(1).split(".")[0]  # strip domain
            local_intf = normalize_intf(local_match.group(1))
            remote_intf = normalize_intf(local_match.group(2))
            neighbors.append({
                "remote_device": remote_name,
                "local_intf": local_intf,
                "remote_intf": remote_intf,
            })
    return neighbors


# -----------------------------------------------------------------------
# Topology builder
# -----------------------------------------------------------------------
def build_topology(input_dir):
    """Read all .txt files in input_dir and build devices + links."""
    devices = {}  # name -> {role, tier, interfaces}
    links = []    # [{a_device, a_intf, b_device, b_intf}]
    seen_links = set()

    txt_files = sorted(
        f for f in os.listdir(input_dir)
        if f.endswith(".txt") and not f.startswith("prompt")
    )

    for fname in txt_files:
        path = os.path.join(input_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        name = parse_device_header(text)
        sections = extract_sections(text)
        role = detect_role(name, sections)
        tier = classify_tier(name)

        ip_intf = {}
        if "show ip interface brief" in sections:
            ip_intf = parse_ip_interfaces(sections["show ip interface brief"])

        devices[name] = {
            "role": role,
            "tier": tier,
            "interfaces": ip_intf,
        }

        # Parse CDP neighbors for link discovery
        if "show cdp neighbors detail" in sections:
            cdp_neighbors = parse_cdp_neighbors(
                sections["show cdp neighbors detail"]
            )
            for nbr in cdp_neighbors:
                # Create a canonical link key to avoid duplicates
                pair = tuple(sorted([
                    (name, nbr["local_intf"]),
                    (nbr["remote_device"], nbr["remote_intf"]),
                ]))
                if pair not in seen_links:
                    seen_links.add(pair)
                    links.append({
                        "a_device": name,
                        "a_intf": nbr["local_intf"],
                        "b_device": nbr["remote_device"],
                        "b_intf": nbr["remote_intf"],
                    })

    return devices, links


# -----------------------------------------------------------------------
# Layout calculator
# -----------------------------------------------------------------------
def compute_positions(devices):
    """Assign x, y positions based on tier grouping."""
    tiers = {}
    for name, info in devices.items():
        tier = info["tier"]
        tiers.setdefault(tier, []).append(name)

    positions = {}
    sorted_tiers = sorted(tiers.keys(), key=lambda t: TIER_ORDER.get(t, 99))

    for tier_idx, tier in enumerate(sorted_tiers):
        members = sorted(tiers[tier])
        tier_width = len(members) * H_SPACING
        start_x = LEFT_MARGIN + (3 * H_SPACING - tier_width) // 2
        y = TOP_MARGIN + tier_idx * V_SPACING

        for i, name in enumerate(members):
            x = start_x + i * H_SPACING
            positions[name] = (x, y)

    return positions


# -----------------------------------------------------------------------
# Draw.io XML generator
# -----------------------------------------------------------------------
EDGE_LABEL_STYLE = (
    "edgeLabel;html=1;align=center;verticalAlign=middle;"
    "resizable=0;points=[];fontSize=10;"
)


def build_endpoint_label(device_name, intf, devices):
    """Build a label for one end of a link: 'E0/0 (10.0.12.1)' or just 'E0/0'."""
    short = shorten_intf(intf)
    ip = devices.get(device_name, {}).get("interfaces", {}).get(intf, "")
    if ip:
        return short + "\n" + ip
    return short


def generate_drawio(devices, links, positions, output_path):
    """Generate the .drawio XML file."""
    mxfile = ET.Element("mxfile")
    diagram = ET.SubElement(mxfile, "diagram", id="topology", name="Network Topology")
    model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": "0", "dy": "0", "grid": "1", "gridSize": "10",
        "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1",
        "fold": "1", "page": "1", "pageScale": "1",
        "pageWidth": "1100", "pageHeight": "850",
        "math": "0", "shadow": "0",
    })
    root = ET.SubElement(model, "root")

    # Mandatory structural cells
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    # Device IDs for referencing in edges
    device_ids = {}
    cell_id = 2

    # Create device nodes
    for name, info in sorted(devices.items()):
        did = "d" + str(cell_id)
        device_ids[name] = did
        cell_id += 1

        style = SWITCH_STYLE if info["role"] == "switch" else ROUTER_STYLE
        x, y = positions.get(name, (100, 100))

        cell = ET.SubElement(root, "mxCell", {
            "id": did,
            "value": name,
            "style": style,
            "vertex": "1",
            "parent": "1",
        })
        ET.SubElement(cell, "mxGeometry", {
            "x": str(x), "y": str(y),
            "width": str(NODE_W), "height": str(NODE_H),
            "as": "geometry",
        })

    # Create link edges with endpoint labels
    for link in links:
        eid = "e" + str(cell_id)
        cell_id += 1

        source_id = device_ids.get(link["a_device"])
        target_id = device_ids.get(link["b_device"])

        # Skip links to devices we don't have collected data for
        if not source_id or not target_id:
            continue

        # Edge line (no centered label)
        cell = ET.SubElement(root, "mxCell", {
            "id": eid,
            "value": "",
            "style": EDGE_STYLE,
            "edge": "1",
            "parent": "1",
            "source": source_id,
            "target": target_id,
        })
        ET.SubElement(cell, "mxGeometry", {
            "relative": "1",
            "as": "geometry",
        })

        # Source-side label (near device a, but not overlapping name)
        src_label_id = eid + "_src"
        src_label = build_endpoint_label(
            link["a_device"], link["a_intf"], devices
        )
        src_cell = ET.SubElement(root, "mxCell", {
            "id": src_label_id,
            "value": src_label,
            "style": EDGE_LABEL_STYLE,
            "vertex": "1",
            "connectable": "0",
            "parent": eid,
        })
        src_geo = ET.SubElement(src_cell, "mxGeometry", {
            "x": "-0.4",
            "relative": "1",
            "as": "geometry",
        })
        ET.SubElement(src_geo, "mxPoint", {"as": "offset"})

        # Target-side label (near device b, but not overlapping name)
        tgt_label_id = eid + "_tgt"
        tgt_label = build_endpoint_label(
            link["b_device"], link["b_intf"], devices
        )
        tgt_cell = ET.SubElement(root, "mxCell", {
            "id": tgt_label_id,
            "value": tgt_label,
            "style": EDGE_LABEL_STYLE,
            "vertex": "1",
            "connectable": "0",
            "parent": eid,
        })
        tgt_geo = ET.SubElement(tgt_cell, "mxGeometry", {
            "x": "0.4",
            "relative": "1",
            "as": "geometry",
        })
        ET.SubElement(tgt_geo, "mxPoint", {"as": "offset"})

    # Write pretty-printed XML
    rough = ET.tostring(mxfile, encoding="unicode")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ")
    # Remove the extra XML declaration minidom adds
    lines = pretty.splitlines()
    if lines and lines[0].startswith("<?xml"):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate a draw.io network diagram from collected show output"
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Path to the collector output directory (e.g., output/2026-03-14_131951/)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output .drawio file path (default: <input-dir>/network-topology.drawio)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print("[ERROR] Input directory not found: " + args.input_dir)
        return

    output_path = args.output
    if not output_path:
        output_path = os.path.join(args.input_dir, "network-topology.drawio")

    print("=" * 60)
    print("  GTT Network Diagram Generator")
    print("  EP004 - G Talks Tech")
    print("=" * 60)
    print("")
    print("[*] Reading collected output from: " + args.input_dir)

    devices, links = build_topology(args.input_dir)

    print("[*] Found " + str(len(devices)) + " devices:")
    for name, info in sorted(devices.items()):
        intf_count = len(info["interfaces"])
        print("    " + name + " (" + info["role"] + ", tier: " + info["tier"] + ", " + str(intf_count) + " IPs)")

    print("[*] Found " + str(len(links)) + " links:")
    for link in links:
        print(
            "    " + link["a_device"] + " " + shorten_intf(link["a_intf"])
            + " <-> "
            + link["b_device"] + " " + shorten_intf(link["b_intf"])
        )

    positions = compute_positions(devices)

    generate_drawio(devices, links, positions, output_path)
    print("")
    print("[+] Diagram saved to: " + output_path)
    print("    Open in draw.io (desktop or app.diagrams.net).")
    print("    Tip: use Arrange > Layout > Vertical Tree to auto-adjust.")


if __name__ == "__main__":
    main()
