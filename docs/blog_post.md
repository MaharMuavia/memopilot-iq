# Building a Memory Layer That Can Explain Itself

> Publish only after running the final benchmark and adding the generated report
> and Alibaba Cloud deployment evidence. Do not replace the placeholders below
> with hand-entered metrics.

Most AI assistants have short-lived context, but durable memory introduces a
different problem: what should remain, what should be retired, and how can a
user inspect the decision? MemoPilot IQ approaches this as a memory-governance
layer rather than a chat-history archive.

The system turns selected dialogue into typed records such as preferences,
decisions, constraints, and deadlines. Each record has a lifecycle state. A
later decision can supersede an earlier one; temporary information can expire;
users can archive, delete, export, or erase a project. At answer time, hybrid
retrieval and an interpretable score assemble only the records that fit the
configured context budget. The UI exposes a Memory Trace showing what was used
or skipped and why.

Qwen handles chat, structured memory extraction, and embeddings through the
DashScope-compatible API. The local mode deliberately has no credential
requirement so contributors can run the system and its tests offline. The cloud
adapter targets Alibaba Tablestore for memory records and OSS for redacted turn
snapshots; its live deployment must be evidenced separately.

The part I care about most is being able to falsify the system's claims. The
repository includes a 24-scenario diagnostic that runs both the memory-enabled
path and a no-memory baseline. It reports strict answer checks, whether target
facts reached the assembled context, stale-memory leaks, historical-context
reduction, and latency. The benchmark dashboard shows the report produced by
the current build, rather than displaying fixed marketing figures.

This is not a claim that an agent should remember everything. It is a claim
that long-term memory should be inspectable, bounded, and reversible. The next
step is to run the final model-backed benchmark, publish the raw result, and
include the cloud health and storage evidence with the deployment.

**Repository:** https://github.com/MaharMuavia/memopilot-iq
**Built with:** Qwen Cloud, FastAPI, React, and Alibaba Cloud adapters
