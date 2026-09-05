# Local Agent Harness: Follow Along

Stand up an AI agent harness on hardware you own, point it at a local model,
and wire it to real network tools through MCP. No cloud API, no device data
leaving the machine.

> ### Read this first: results are not in yet
>
> This is a **follow-along**, not a finished runbook. It is the setup path and
> the open questions for a video that has not been recorded. Every step below
> is either a verified command or a clearly-labeled thing we are about to test.
>
> **The central question is genuinely unanswered:** we do not yet know whether
> a local model is reliable enough to drive tools. If it turns out it is not,
> that is the finding and we will publish it that way.
>
> Nothing here claims a working harness. When the lab settles it, this folder
> gets the real runbook with measured numbers.

> **Mailing list:** [join.gtalkstech.com](https://join.gtalkstech.com) -- the
> finished runbook ships there first.

## Prereqs

- [Ollama](https://ollama.com) with at least one tool-capable model pulled
- A machine with enough RAM to hold the model plus a real KV cache. Tool
  loops use far more context than a single-shot prompt does.
- Optional, for the tool half: the read-only MCP server from the previous
  episode's kit, in
  [`local-ai/local-ai-network-engineers/`](../local-ai-network-engineers/).
  It exposes two tools, one live ping and one cached config parse, and it is
  read-only by design.

## Step one: install Goose

```bash
curl -fsSL https://github.com/aaif-goose/goose/releases/download/stable/download_cli.sh | bash
```

Then check what you got:

```bash
goose --version
```

**Use v1.49.0 or newer.** Version matters more than usual here, because the
approval behavior has moved three times in six weeks:

| Version | Date | What changed that matters |
|---|---|---|
| v1.46.0 | 2026-08-12 | Fixes silent empty-turn termination ([#10353](https://github.com/aaif-goose/goose/issues/10353)). Below this, a run can stop with no error at all. |
| v1.48.0 | 2026-08-27 | Permission denies take precedence ([#11477](https://github.com/aaif-goose/goose/pull/11477)). A persisted deny now beats a conflicting allow. |
| v1.49.0 | 2026-09-03 | Shows tool inputs before approval ([#10932](https://github.com/aaif-goose/goose/issues/10932)) and enforces per-turn model tool allowlists ([#11426](https://github.com/aaif-goose/goose/issues/11426)). |

That last one is worth pausing on. Seeing the arguments before you approve is
the difference between approving "it wants to run a tool" and approving "it
wants to run this, with these values."

## Step two: point it at Ollama

```bash
export GOOSE_PROVIDER=ollama
export GOOSE_MODEL=<your-model>
```

**Set your context window before you do anything else.** Ollama's default
context is small enough to silently truncate a real tool loop, and the failure
does not announce itself. There is a long-running report of exactly this
against Goose ([#1253](https://github.com/aaif-goose/goose/issues/1253)). The
Ollama server log is where the truncation line shows up.

The environment block that fixes this, with the reasoning behind each setting,
is in the previous kit's
[quickstart runbook](../local-ai-network-engineers/local-ai-quickstart-runbook.md),
sections one and two.

## Step three: find out where your config actually lives

Before you configure anything, look:

```bash
ls -la ~/.config/goose/
cat ~/.config/goose/*.yaml
```

**This is an open question, not an instruction.** The documentation describes
configuration living in `config.yaml`. There is a report
([#5196](https://github.com/aaif-goose/goose/issues/5196)) that permissions
actually live in a separate `permission.yaml` and secrets in `secrets.yaml`,
and that people who follow the docs end up with permission rules that silently
do nothing.

We have not confirmed this on disk yet. That is one of the things this lab
session is for. If you run it before we do, your file listing is the answer,
and we would genuinely like to hear what you got.

## Step four: wire a tool server

Register an MCP server as an extension in your Goose config, over stdio.

If you want a network-shaped one that cannot hurt anything, use
[`netops-mcp-server.py`](../local-ai-network-engineers/netops-mcp-server.py)
from the previous kit. Two tools, read-only, and one of them runs against
cached captures so you can follow along with no lab at all.

Then set the mode that makes the boundary visible:

```bash
export GOOSE_MODE=approve
```

Confirm the prompt fires **before** each tool call, not after. That ordering is
the whole point.

## Step five: look hard at the boundary

This is what the video is actually about, so here is what to watch rather than
what to conclude.

**Set an explicit rule, then try to get around it.** There is a report
([#11017](https://github.com/aaif-goose/goose/issues/11017)) that in
`smart_approve` mode, the classifier deciding whether a command is safe can run
past an explicit user-configured ask rule. The reporter allowed two read-only
git commands, set ask-on-everything-else, and watched a third command run with
no prompt because the classifier judged it harmless. It was closed as not-a-bug
on 2026-08-11.

Whether it still reproduces on current versions is one of the things we are
testing. Try it yourself and see. A permission prompt is a seatbelt, not a law
of physics, and the interesting question is always what the gate is made of.

## The comparison: LM Studio's Bionic

Bionic is worth setting up next to Goose, because the two gates are built
differently.

- Bionic **does** support MCP. Confirmed against
  [LM Studio's MCP documentation](https://lmstudio.ai/docs/app/mcp) and
  [Cloudflare's Bionic agent setup page](https://developers.cloudflare.com/agent-setup/bionic/).
  It shows a confirmation dialog before a tool call runs, with per-tool
  whitelisting.
- As of **1.1.0** (2026-08-27) it has a named four-mode shell approval
  spectrum: disabled, manual review, auto review, and allow-all, with
  persistent preferences. Current release is **1.1.1** (2026-08-31), which is
  interface and performance work and does not change the approval mechanics.

One honest note about pace: Bionic shipped three times in under two weeks while
this page was being prepared. Check the version you actually have before
trusting anything written about it, including this page.

## Known rough edges

Real, filed, and worth knowing before you blame your own setup:

- [#1253](https://github.com/aaif-goose/goose/issues/1253) -- Ollama context truncation, silent
- [#10353](https://github.com/aaif-goose/goose/issues/10353) -- empty-turn termination, fixed in v1.46.0 and later
- [#8272](https://github.com/aaif-goose/goose/issues/8272) -- tool-call JSON parse failures
- [#8275](https://github.com/aaif-goose/goose/issues/8275) -- toolshim interpreter no-op
- [#6883](https://github.com/aaif-goose/goose/issues/6883) -- some models abandon JSON and emit XML-style tags once the registered tool count climbs

## Security

One published advisory as of today:
[GHSA-r5pp-p5r8-466r](https://github.com/aaif-goose/goose/security/advisories)
(High, 2026-07-24), arbitrary command execution in `goose review` through git
`core.fsmonitor`. That is the only one. If you see a CVE number attached to this
project somewhere, check it against the repository's own advisory page before
repeating it.

## What we do not know yet

Stated plainly, because this is the part most write-ups skip:

- **Whether a local model in this class drives tools reliably enough to trust.**
  Unmeasured. Published tool-calling benchmarks measure older model
  generations, so we are not repeating their numbers as though they were ours.
- **Where permissions actually live on disk.** See step three.
- **Whether the classifier still walks past explicit rules.** See step five.
- **What each approval gate is actually made of**, once two of them sit side by
  side against the same tools.

Answers, with measurements, when the lab is done.

---

*Part of [netops-toolkit](https://github.com/GTalksTech/netops-toolkit) from
[G Talks Tech](https://www.youtube.com/@GTalksTechOfficial). The companion
video link lands here when it publishes.*
