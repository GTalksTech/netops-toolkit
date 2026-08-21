# Local AI Prompt Pack for Network Engineers

**Version 1.0**
**Released:** 2026-08-21
**Author:** Garrett Masters, G Talks Tech
**Website:** https://gtalkstech.com
**Mailing list:** https://join.gtalkstech.com

Prompts and prompt adjustments for running network engineering work on LOCAL
models (Ollama, LM Studio, and friends). Local models are smaller and more
literal than the frontier cloud models, and they reward a different prompting
style: stripped-down personas, explicit negative constraints, and structure
the model cannot wander away from.

Everything labeled **tested** below was run against real lab configs on a
local model and verified line by line. The rest is technique guidance --
sound practice, clearly marked, for you to verify on your own setup.

---

## Safety labels, local edition

The house rule for AI prompts is two labels: **Public-safe** (needs no real
device data) and **Enterprise-only** (needs real configs, IPs, hostnames, or
live output -- never paste those into a free cloud tier that trains on
inputs).

**On a local model, that distinction collapses -- that is the entire point.**
When the model runs on your own hardware and you have verified nothing leaves
the machine (the companion runbook's section 6 shows you how to verify, not
assume), pasting a real config into it is your laptop talking to your laptop.

So every prompt in this pack is safe with real data **on a verified-local
model**. If you take any of these prompts to a cloud model instead, the
standard labels snap back into force: these prompts want real configs, which
makes every one of them **Enterprise-only** in the cloud. Paid tier,
no-training commitment, or don't paste.

One more local-specific check before you trust the "local" part: cloud-hosted
models can live inside local apps (Ollama's `:cloud` tags). Check the tag.

---

## 1. The documentation handoff prompt (tested)

The flagship. Run against a real 14K-token `show run all` capture, this
produced an interface table, routing summary, and risk list with **zero
hallucinations** -- every claim verified at a real line number.

```text
You are documenting a network device for an engineer handoff. From the
following running configuration, produce:
1) an interface table (name, IP, mask, description, state),
2) a routing summary (protocols, router-id, networks, passive interfaces),
3) a list of configuration risks or oddities worth an engineer's attention.
Config follows:

[PASTE RUNNING-CONFIG HERE]
```

**When to use:** device handoffs, documentation sprints, "what even is this
box" archaeology.

**Notes:**
- Numbered output requirements do real work on local models -- they anchor
  the structure so a smaller model doesn't drift into prose.
- The risk list is deliberately open-ended ("worth an engineer's attention"),
  and on the tested runs it earned its place: real findings at real line
  numbers, several of which a cloud model's noise-filtering skipped.
- Verify every claim against the config before it ships. On one tested run at
  large context the model confidently misread an explicit
  `passive-interface` line. The draft is free; the review is your job.

## 2. The extraction prompt (tested)

For when you want data, not documentation:

```text
Extract every interface that has an IPv4 address from this running-config.
For each, report: interface name, IP address, subnet mask. Use ONLY
information present in the config. Config:

[PASTE RUNNING-CONFIG HERE]
```

**Tested result:** 8/8 runs clean across two models and two sampling
profiles -- zero fabricated IPs, zero missed.

**Notes:**
- "Use ONLY information present in the config" is the load-bearing negative
  constraint. Cheap to include, and it gives the model an explicit license to
  omit rather than guess.
- For pipeline use, pair with `temperature 0` -- tested runs at temp 0 were
  token-identical across repeats, which is what you want when the output
  feeds a diff.

## 3. The compiler persona (for structured extraction)

Small local models carry conversational habits that ruin machine-readable
output: preambles, apologies, "Here's your JSON!". Strip the elasticity out
by casting the model as a machine interface:

```text
You are a configuration parser. You are not an assistant. Output ONLY the
requested data structure. No preamble, no explanation, no markdown fences,
no text before or after. If a field is not present in the input, output
null for that field. Never infer or invent values.
```

Prepend to any extraction prompt (or set as the system prompt) when output
goes to a parser instead of a person.

**Better still: don't rely on the persona alone.** Ollama's `format=<JSON
schema>` parameter constrains output at generation time, and that path IS
tested: schema honored, Pydantic-validated, exact ground-truth match. One
critical gotcha on thinking models: set `think: false` on extraction calls,
or you get an empty response with a success status code. Working code ships
alongside this pack (`structured-output-test.py`).

## 4. Chunk by stanza, never by sliding window

Configs are hierarchical. An arbitrary character-window split orphans
sub-commands from their parents (`ip address ...` with no `interface` line
above it), and an orphaned line forces the model to guess context --
which is where hallucination comes from.

When a config exceeds your context budget:

- Split at stanza boundaries: interface blocks, router processes, ACLs,
  line/vty sections. In IOS-style configs, top-level commands start at
  column 0 and children are indented -- split where column 0 changes.
- Process each logical section with the same prompt, then merge
  (map-reduce), carrying device name and section name in each chunk's
  header so the model knows what it is holding.
- Before reaching for chunking at all, check whether you actually need it:
  the companion runbook's context-window section exists because the default
  4096-token window silently truncates -- most "the model missed half my
  config" cases are that, not a real size limit.

## 5. The deterministic-first pattern

The most reliable local AI pipeline is the one where the model never touches
raw data at all:

> **The diff engine finds the drift; the model explains the impact.**

Let deterministic tooling do what it is perfect at -- parsing, diffing,
extracting -- and hand the model the small, already-correct result to
explain, summarize, or turn into an action plan:

```text
The following is the output of a config diff between the approved baseline
and the running config of an access switch. For each change: explain the
operational impact in one sentence, flag anything that weakens security
posture, and state whether it could explain [SYMPTOM]. Do not speculate
about changes not shown in the diff.

[PASTE DIFF OUTPUT HERE]
```

This inverts the failure economics. A model that extracts from 14K tokens of
raw config can hallucinate anywhere in 14K tokens; a model explaining a
20-line diff can only be wrong about 20 lines -- and you can check all 20.

## 6. The audit prompt (handoff prompt, risk-only variant)

When you only want the risk list:

```text
You are reviewing a device configuration before a maintenance window. From
the following running configuration, list every configuration risk,
inconsistency, or oddity worth an engineer's attention. For each: quote the
exact config line, state the risk in one sentence, and rate it high/medium/
low. Use ONLY information present in the config. Do not invent line numbers
or commands.

[PASTE RUNNING-CONFIG HERE]
```

**Notes:**
- "Quote the exact config line" is the verification hook -- it makes every
  claim checkable with a text search instead of a re-read.
- Tested honestly: local models are exhaustive but flat -- on the measured
  head-to-head, the local model surfaced real findings a frontier cloud
  model filtered out, but the cloud model was better at severity judgment
  and cross-device reasoning. The high/medium/low instruction pushes a local
  model toward triage it won't do unprompted. Sanity-check its ratings.

---

## The adjustments, in one table

| Adjustment | Why local models need it |
|---|---|
| Numbered output requirements | Anchors structure; small models drift |
| "Use ONLY information present in..." | Explicit license to omit instead of guess |
| Compiler persona for extraction | Strips conversational elasticity |
| `format=` + `think: false` + Pydantic | Generation-time structure; the empty-response bug fix |
| `temperature 0` for pipelines | Token-identical reruns (tested), diffable outputs |
| Chunk by stanza | Orphaned sub-commands force hallucination |
| Deterministic-first | Shrinks the surface the model can be wrong about |

---

## License

Free to use, copy, adapt, and redistribute. Attribution appreciated but not
required. Published under the same terms as the rest of
[netops-toolkit](https://github.com/GTalksTech/netops-toolkit).
