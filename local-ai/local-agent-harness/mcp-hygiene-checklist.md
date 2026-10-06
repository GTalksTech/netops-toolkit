# MCP Hygiene Checklist

Ten checks before an MCP server gets read or write access to network gear.
Run them against any server, yours or a vendor's, and against the harness
that will call it. Where a check says "in our lab", it happened on a
three-device CML lab with Goose v1.49.0 and Bionic 1.1.6.

---

**1. Data scope: the server reaches only the devices and data it names.**
Why: our server refuses any device not on a fixed list of three, and a
model with a general shell beside its tools went reading files it was never
pointed at.

**2. Read-only by default: writes are separate tools, few, and reversible.**
Why: our one write tool sets an interface description in running-config
only, and the agent still offered, unprompted, to copy running-config to
startup-config.

**3. Provenance: every answer from cached data says where it came from and
how old it is.**
Why: in our lab the agent reported a months-old config capture as current
until the tool printed the capture's timestamp, and then it flagged the
staleness on its own.

**4. Complete output: the tool returns everything, not just the rows that
looked interesting.**
Why: when our interface tool dropped interfaces with no IP address, the
model got one of them right two times out of five; with every interface
returned, three out of three (one of those runs already had the answer in
context).

**5. Honest annotations: a tool that writes does not call itself read-only.**
Why: a harness may use the `readOnlyHint` label to decide whether to ask
(Goose checks it before asking its local model), and the MCP spec tells
clients to treat annotations as untrusted unless the server is trusted.

**6. Per-tool rules in the harness: you set a rule for every tool, reads
included.**
Why: Goose checks your own rule before anything else, and with no rules set
one simple task threw three approval dialogs, which is how people end up
clicking Always Allow on everything.

**7. The gate itself: confirm the harness gates MCP tool calls at all, and
check its default mode.**
Why: Goose ships in a mode that asks about nothing, and in Bionic 1.1.6 our
MCP write ran with no prompt in every mode we tried; its command-approval
menu covers shell commands.

**8. Audit trail: every write leaves a record you did not have to ask the
agent for.**
Why: our write tool returns the interface config before and after the
change, and we still verified each write from a second terminal rather than
taking the agent's word.

**9. Rollback: you know the undo before the first write, and it works
without the agent.**
Why: every change here is one `no description` away from gone and never
reaches startup-config, so a bad write costs a minute, not an outage.

**10. Tool-output trust: treat what the model says about tool output as a
claim to check.**
Why: in our lab the model blamed an SSH timeout on a "transient blip" it had
no evidence for, and named the wrong MCP server as its source, both with
full confidence.
