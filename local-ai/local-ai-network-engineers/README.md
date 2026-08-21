# Local AI for Network Engineers

Run a local AI model on hardware you own and do real network engineering work
with it -- documentation from configs, structured extraction, config audits --
with zero device data leaving the machine.

> **Companion video:** [Stop Redacting Configs for ChatGPT. Run the Model Locally Instead.](https://youtu.be/dDE8gajTKkQ)
>
> **Mailing list:** [join.gtalkstech.com](https://join.gtalkstech.com) -- the
> prompt pack is also delivered there, plus release emails when artifacts ship.

## What's in this folder

| File | What it is |
|---|---|
| [local-ai-quickstart-runbook.md](local-ai-quickstart-runbook.md) | The main artifact: install to verified-private in eight sections, dual-platform (macOS + Windows), built around four silent failures with detection and fixes. Every number measured live. |
| [local-ai-prompt-pack.md](local-ai-prompt-pack.md) | Prompts and prompt adjustments for local models: the tested documentation handoff prompt, extraction, compiler persona, chunk-by-stanza, deterministic-first. |
| `core-rtr-01.cfg`, `edge-rtr-01.cfg`, `access-sw-01.cfg` | Real `show run all` captures from the lab (Cisco IOS, RFC1918 addressing, public by design). The demo inputs. |
| `all-three-devices.cfg` | All three configs combined (~45K tokens) -- the context-ceiling stress file. |
| `sampling-ab-test.py` | Machine-scored A/B of default vs strict sampling on real config extraction. Stdlib only. |
| `structured-output-test.py` | The `format=` + Pydantic structured extraction pattern, including the think=false fix. |
| `netops-mcp-server.py` | Minimal read-only MCP server (ping + parse cached configs) for driving real tools from a local model behind a confirmation dialog. |
| `requirements.txt` | The two pip packages the optional scripts need. |
| `cml-topology.yaml` | Optional: the CML lab the config captures came from (two IOL routers + one IOL-L2 switch). Only needed if you want to replicate the live-ping MCP demo against real devices; everything else runs from the cached captures. |

## Quick start (no lab required)

1. Install Ollama and apply the environment block -- runbook sections 1-2.
   Do not skip the environment block; the default 4096-token context window
   silently truncates config-sized prompts.
2. Pull a model sized to your RAM (runbook section 4 -- check `ollama show`
   for MoE vs dense; it matters more than parameter count).
3. Run the demo against the included capture:

```bash
ollama run qwen3.6:35b --verbose "You are documenting a network device for an engineer handoff. From the following running configuration, produce: 1) an interface table (name, IP, mask, description, state), 2) a routing summary (protocols, router-id, networks, passive interfaces), 3) a list of configuration risks or oddities worth an engineer's attention. Config follows: $(cat core-rtr-01.cfg)"
```

Expect ~18 seconds of silence while it ingests the config (that's prompt
eval, not a hang), then a full handoff doc. Then verify the output against
the config -- the runbook explains why that step is never optional.

## Prereqs

- [Ollama](https://ollama.com) (macOS, Windows, or Linux)
- For the two test scripts and the MCP server: Python 3.10+ and
  `pip install -r requirements.txt`
- No network lab needed -- the config captures stand in for live devices.
  The configs use real RFC1918 lab addressing and the lab's published
  credentials by design, so everything replicates as-is.

## The honest boundary

Measured, not asserted: on documentation-from-configs, a current-generation
local model matched a frontier cloud model on trustworthiness (both zero
hallucinations on the same real config), private and free. The cloud model
was ~6x faster end to end and better at judgment calls (severity, cross-device
reasoning); the local model was more exhaustive on low-level findings.
Neither removes the need for engineer review -- each fumbled something the
other caught. Local wins bounded extraction and explanation tasks; cloud wins
open-ended multi-step reasoning. Pick per task, not per ideology.
