# Local AI for Network Engineers -- Quickstart Runbook

**Version 1.0**
**Released:** 2026-08-21
**Author:** Garrett Masters, G Talks Tech
**Website:** https://gtalkstech.com
**Mailing list:** https://join.gtalkstech.com

Stand up a local AI model on hardware you own and run a real
documentation-from-configs workflow with zero data leaving the machine. Every
number in this runbook was measured live on a MacBook Pro M3 Max with 64 GB of
unified memory. The Windows blocks give the documented equivalent mechanics for
each step; the measurements themselves are from the Mac.

The spine of this runbook is four silent failures. Local model tooling fails
quietly: no error, no warning, just wrong or missing output that looks fine.
Each one below comes with detection and a fix, because the failure you can't
see is the one that ends up in your documentation.

---

## Contents

1. [Install (and the gotcha in the first sixty seconds)](#1-install)
2. [The verified environment block](#2-the-verified-environment-block)
3. [The four silent failures](#3-the-four-silent-failures)
4. [Picking a model: architecture beats parameter count](#4-picking-a-model)
5. [Extraction settings for pipelines](#5-extraction-settings-for-pipelines)
6. [Verify the privacy claim yourself](#6-verify-the-privacy-claim-yourself)
7. [macOS Local Network permission (for MCP and agent tools)](#7-macos-local-network-permission)
8. [Replication kit: run the exact demo](#8-replication-kit)

---

## 1. Install

**macOS:**

1. Download Ollama from https://ollama.com and drag it to Applications.
2. **Launch the app before you open a terminal.** The `ollama` CLI is
   installed on first app LAUNCH, not on drag-to-Applications. If you drag,
   open a terminal, and type `ollama`, you get `command not found` and nothing
   tells you why. Launch the app once; the CLI appears.
3. Pull a model: `ollama pull qwen3.6:35b` (24 GB -- see section 4 before
   committing to a model for your RAM size).

Pulls resume if interrupted. A 40+ GB model download can be stopped and
restarted without losing progress.

**Windows:**

1. Download the Ollama installer from https://ollama.com and run it. The
   installer puts `ollama` on your PATH and starts the background service.
2. Verify in a NEW terminal: `ollama --version`.
3. Pull the same way: `ollama pull qwen3.6:35b`.

---

## 2. The verified environment block

Ollama ships with defaults tuned for chat toys, not 14,000-token router
configs. Every variable below is confirmed against Ollama's current docs and
was run live. Set them BEFORE your first serious session.

**macOS** (launchctl values are read at app launch -- restart the Ollama app
after setting):

```bash
launchctl setenv OLLAMA_CONTEXT_LENGTH 65536
launchctl setenv OLLAMA_FLASH_ATTENTION 1
launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0
launchctl setenv OLLAMA_NUM_PARALLEL 1
launchctl setenv OLLAMA_KEEP_ALIVE -1
```

**Windows** (setx writes user environment variables; restart the Ollama app
from the system tray afterward -- new values only reach processes started
after the change):

```powershell
setx OLLAMA_CONTEXT_LENGTH 65536
setx OLLAMA_FLASH_ATTENTION 1
setx OLLAMA_KV_CACHE_TYPE q8_0
setx OLLAMA_NUM_PARALLEL 1
setx OLLAMA_KEEP_ALIVE -1
```

**Verify it took** (both platforms): run any model with `--verbose` and check
the server picked up the context length, or query the API:

```bash
ollama run qwen3.6:35b --verbose "say ok"
```

**Why each one matters:**

| Variable | Value | Why |
|---|---|---|
| `OLLAMA_CONTEXT_LENGTH` | 65536 | The default is **4096 tokens** -- the single biggest trap in local AI. See silent failure (b). 65536 fits a two-device config paste plus a full answer. On 16-32 GB machines use 32768; KV cache costs RAM. |
| `OLLAMA_FLASH_ATTENTION` | 1 | Required for the quantized KV cache below to help instead of hurt. Without it the engine dequantizes on every attention step. |
| `OLLAMA_KV_CACHE_TYPE` | q8_0 | Halves KV cache memory at effectively no quality cost. Needs Flash Attention ON. |
| `OLLAMA_NUM_PARALLEL` | 1 | Higher values pre-allocate a separate KV cache PER concurrent request and will exhaust your memory instantly. One user, one slot. |
| `OLLAMA_KEEP_ALIVE` | -1 | Keeps the model loaded instead of unloading after 5 minutes. Model swaps are visible pauses (measured: ~18.5 s to reload a 24 GB model after eviction). |

---

## 3. The four silent failures

These all happened live, on camera, on a well-configured machine. None of them
produced an error message.

### (a) `$(cat missing-file)` runs an EMPTY prompt

```bash
ollama run qwen3.6:35b "Document this config: $(cat wrong-path.cfg)"
```

If the file path is wrong, the shell substitution fails, the prompt runs
WITHOUT the config, and the model answers anyway. A polite model asks where
the config is; a weaker one may fabricate an answer about a config it never
saw. The command exits zero either way.

- **Detect:** the response arrives suspiciously fast, or the model asks for
  the config / answers generically.
- **Fix:** `cat` the file by itself first, or check the `prompt eval count`
  stat (with `--verbose`) against the rough size of what you sent.

### (b) The default 4096 context FRONT-truncates -- your question is the first thing discarded

Measured live: a 14,301-token config sent into a default 4096 window showed
`prompt eval count: 2050`. Roughly 12,000 tokens were silently discarded from
the FRONT of the prompt -- which is where the question was. The model received
the tail of the config with the first word of the question glued to an SSH
line, diagnosed that remnant as a paste error in the config, summarized the
half it could see, and asked what we wanted. Confident, helpful, and working
on 14% of the input. No warning at any point.

- **Detect:** `--verbose` prints `prompt eval count`. Compare it to what you
  sent (rule of thumb from these measurements: a 44 KB `show run all` is
  ~14K tokens, so ~3 tokens per byte-of-config divided by 10).
- **Fix:** the environment block above. This failure is why
  `OLLAMA_CONTEXT_LENGTH` leads it.

### (c) The context window fills mid-answer -- generation stops with no error

The window must hold your prompt PLUS the model's thinking PLUS the answer.
Measured live: a 28,391-token paste into a 32K window generated healthy output
and then stopped mid-table at 28,391 + 4,377 = 32,768 tokens exactly. HTTP
200, no error, a table that just ends.

Thinking models spend the window twice -- reasoning tokens and answer tokens
both count.

- **Detect:** output ends mid-sentence or mid-table; `prompt eval count` +
  `eval count` equals your context limit exactly.
- **Rule:** keep roughly one third of the window free for the response.

### (d) Thinking + `format=` = empty response with HTTP 200

Structured output (`format=<JSON schema>`) on a model that thinks by default
returns an EMPTY string with a success status code. Confirmed live on three
consecutive runs.

- **Detect:** `response` is `''` but the HTTP call succeeded.
- **Fix:** set `think: false` on extraction calls. With thinking off, the same
  schema returned valid JSON that matched ground truth exactly. (See
  `structured-output-test.py` in this folder for the working pattern.)

---

## 4. Picking a model

**Architecture beats parameter count.** Measured on the same machine, same
prompt, machine quiet:

| Model | Architecture | Measured eval tok/s |
|---|---|---|
| laguna-xs-2.1 | MoE (33B total / 3B active) | 74.99 |
| qwen3-coder:30b | MoE (30B / 3.3B active) | 65.54 |
| qwen3.6:35b | MoE (36B) | 59.73 |
| gpt-oss:20b | MoE | 58.18 |
| qwen3.6:27b | Dense (27.8B) | 15.30 |
| llama3.3:70b | Dense (70B) | 6.78 |

The 35B model is 4x FASTER than the 27B model from the same family on
identical hardware, because the 35B is Mixture-of-Experts and the 27B is
dense. Every fast model on that ladder is MoE; every slow one is dense.

**The model page will not tell you the architecture.** Check it yourself:

```bash
ollama show qwen3.6:35b
```

Read the architecture field. `qwen35moe` vs `qwen35` was the entire
difference between usable and painful above.

**What your RAM honestly runs** (community-reported paths, not measured here
-- the M3 Max 64 GB row is the measured baseline of this runbook):

- **16 GB:** ~9B-class models. Real, but limited context headroom.
- **32 GB:** 20-30B MoE class at interactive speed. The sweet spot for cost.
- **64 GB:** 30-35B MoE fast (~60-75 tok/s measured), dense 70B loads but
  crawls (~7 tok/s measured -- usable for "let it think" jobs, not
  interactive work).

Leave headroom. A model that barely fits leaves nothing for the KV cache, and
context is the thing you actually need for config work.

---

## 5. Extraction settings for pipelines

For extraction tasks (interface tables, structured audits) where you want
reproducible output:

```json
{
  "temperature": 0.0,
  "top_p": 0.1,
  "top_k": 10,
  "repeat_penalty": 1.15
}
```

Plus `format=<your JSON schema>`, `think: false`, and Pydantic validation on
the way out. Working code: `structured-output-test.py` and
`sampling-ab-test.py` in this folder.

**Honest framing, from an 8-run A/B test on real configs:** the strict
settings did NOT reduce hallucinations, because there were none to reduce --
all 8 runs (two models, default AND strict sampling) extracted the interface
table cleanly with zero fabricated IPs. On a well-formed config extraction,
current-generation models didn't need the help. What temp 0 actually bought
was **determinism**: strict runs were token-identical run to run; default
runs varied. Use strict settings as pipeline insurance and for reproducible
diffs, not because you should expect defaults to hallucinate on this class of
task.

The verification habit is the non-negotiable part. In a 64K-context run,
an otherwise-flawless output confidently misread an explicit
`passive-interface Loopback0` line -- the same model got it right at 14K.
Subtle, confident, senior-engineer-catches-it errors are the failure mode.
Review the draft; the engineer signing off is responsible for what ships.

---

## 6. Verify the privacy claim yourself

"Local means private" should be a measurement, not a marketing line. Three
steps, each verifiable on your own machine.

### Verify the default (macOS / Linux)

```bash
sudo lsof -i -P -n | grep -i ollama
```

**Windows equivalent:**

```powershell
Get-Process ollama | ForEach-Object { Get-NetTCPConnection -OwningProcess $_.Id }
```

Measured across a full inference lifecycle (idle, mid-inference,
post-completion), with wifi ON the whole time: every socket was
`127.0.0.1` -- two loopback listeners at idle, three loopback-to-loopback
connections during inference, back to two after. Zero external connections at
any point, with the internet fully available. Every address on that screen is
your laptop talking to your laptop.

### Name the exception

Not everything in your local model app is local. Ollama offers cloud-hosted
models tagged `:cloud` -- those run remotely by definition. Check the tag
before you assume.

### Close the door and prove it closed

Make local-only durable (survives reboot, unlike environment variables):
create or edit `~/.ollama/server.json` (macOS/Linux) or
`%USERPROFILE%\.ollama\server.json` (Windows):

```json
{"disable_ollama_cloud": true}
```

Restart the Ollama app, then prove it:

```bash
ollama run kimi-k3:cloud "hello"
```

Verified result: `Error: ollama cloud is disabled: remote model details are
unavailable`. That refusal is your proof the policy is enforced, not assumed.

---

## 7. macOS Local Network permission

If you wire a local model to network tooling (an MCP server that pings or
polls devices), the tool calls run as CHILD PROCESSES of the host app -- and
child processes inherit the host app's macOS permissions.

**Symptom (hit live):** the agent's ping tool returns `No route to host` for
a LAN device while the same ping works fine in Terminal. The host app (LM
Studio, in the measured case) lacked the Local Network permission; Terminal
had it.

**Fix:** System Settings -> Privacy & Security -> Local Network -> enable the
host app, then relaunch it. After the fix, the same tool call reached the
device (8.5 ms average on the measured run).

This applies to any MCP host app on macOS. If tool calls can't reach things
the terminal can, check the host app's permissions before debugging the tool.

---

## 8. Replication kit

Everything needed to reproduce the documentation demo verbatim is in this
folder -- no lab required.

**Input:** `core-rtr-01.cfg` -- a real `show run all` capture from a Cisco
IOS lab router (~44 KB, ~14K tokens). Companions: `edge-rtr-01.cfg`,
`access-sw-01.cfg`, and `all-three-devices.cfg` (~138 KB, ~45K tokens -- the
deliberate "even a big window has a ceiling" stress file).

**The exact demo prompt:**

```bash
ollama run qwen3.6:35b --verbose "You are documenting a network device for an engineer handoff. From the following running configuration, produce: 1) an interface table (name, IP, mask, description, state), 2) a routing summary (protocols, router-id, networks, passive interfaces), 3) a list of configuration risks or oddities worth an engineer's attention. Config follows: $(cat core-rtr-01.cfg)"
```

**What to expect (measured):** ~18 seconds of silence first -- that is the
model ingesting 14K tokens at ~810 tokens/second of prompt eval, not a hang.
Budget that pause into real use. Then generation at ~50 tok/s: an interface
table, a routing summary, and a risk list.

**Then verify it.** On the measured run, every claim checked out against the
config line by line: 5/5 interfaces exact, routing summary exact, every
flagged risk real at a real line number. Zero hallucinations -- on that run.
Section 5 explains why you check every run anyway.

**The scripts:**

| File | What it does |
|---|---|
| `sampling-ab-test.py` | The 8-run default-vs-strict A/B with machine scoring of fabricated/missed IPs. Stdlib only; needs Ollama running. |
| `structured-output-test.py` | The `format=` + Pydantic extraction pattern, including the think=false fix for silent failure (d). Needs `pydantic`. |
| `netops-mcp-server.py` | A minimal read-only MCP server (ping + parse cached configs) for driving real tools from a local model behind the host app's confirmation dialog. Needs `fastmcp`. |

The MCP server is read-only BY DESIGN: no config-changing tool exists in it on
purpose. A local model driving tools should start behind a confirmation
dialog with nothing destructive to confirm. Note the "always allow" checkbox
in your host app is one click from disabling that boundary -- the
confirmation is a setting, not a guarantee.

---

## License

Free to use, copy, adapt, and redistribute. Attribution appreciated but not
required. Published under the same terms as the rest of
[netops-toolkit](https://github.com/GTalksTech/netops-toolkit).
