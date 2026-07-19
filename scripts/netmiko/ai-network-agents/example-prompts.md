# Demo prompts, in order

The exact prompts from the video's audit run, with what each one exercises.
Type them into your MCP host once the `netagent` server is connected.

## 1. The sweep

> Audit my home lab and tell me what's wrong. Worst things first.

One plain-English ask, no method. The agent picks the tools, runs the posture
sweep, and returns a ranked worst-first story instead of a raw findings dump.
Watch for the CVE provenance line: the data comes from Cisco's live PSIRT
openVuln API when credentials are set, or the honestly-labeled frozen cache
when they are not.

## 2. The showpiece

> Explain the top finding. How did you catch it?

The cross-device gap: one router's ACL guards the server subnet while the
other router routes around it. The server's heuristic flags it as a candidate;
the agent confirms it by reading both configs. Ask it to check reachability
and it verifies with read-only commands before asserting anything.

## 3. The CVE, honestly scoped

> Talk to me about the top CVE finding, the HTTP one. What should I do?

Expect an honest exploitability read (not just the CVSS number), the
mitigation-versus-patch distinction, and a concrete recommendation.

## 4. A refusal that is working as designed

> Go ahead and fix the NTP finding on the core router.

The server returns `human_author_required` -- a clean result, not an error.
Some changes must be authored and reviewed by a human, and the server says so
itself.

## 5. Propose, approve, apply

> Let's do the HTTP fix on the core router. Propose it.

The agent renders a dry-run diff and stops at the approval gate with an
approval ID. Approve it explicitly, by name, with a reason:

> I approve <approval-id>. Approver: <your name>. Reason: web UI unused,
> removing the attack surface.

The apply goes through for that one device only, then the agent verifies by
reading the config back.

## 6. The receipt

> Show me the audit log.

Every call, allowed or blocked, in an append-only JSONL file on disk, plus a
reviewable approval artifact per change. The story to look for: the same apply
call recorded twice with opposite outcomes, one human approval apart.
