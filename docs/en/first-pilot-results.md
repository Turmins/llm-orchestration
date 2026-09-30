# First Pilot: Observed Results and Measurement Limits

Version: 2026-09-30. Status: a real, bounded answer-only pilot completed; the planned CLI/App Server technical fixture and economic comparison remain incomplete.

## 1. Independent conclusion

Both requested configurations, W = GPT-6 Luna and E = GPT-6.1 Sol at `medium`, returned correct answers for all six fixed synthetic tasks on their first batch attempt. W-only and E-only each scored 6/6. W→E also accepted 6/6 using the same initial W checkpoint; its escalation condition never occurred. This is not evidence that escalation works or that the models have equal general capability.

The question about “20 times” was not an assumed outcome. Rates were checked independently, and correctness criteria were fixed before comparative calls. No paid API calls, purchases, credits, or account changes were initiated. Actual subscription consumption was not exposed and is **unknown**, not zero. No orchestrator was implemented.

## 2. Verified prices

Standard API, USD per one million tokens, ordinary context bracket, checked on 2026-09-30:

| Token category | GPT-6 Luna | GPT-6.1 Sol | Sol/Luna |
|---|---:|---:|---:|
| Ordinary input | $0.10 | $2.00 | 20× |
| Cache read | $0.01 | $0.10 | 10× |
| Cache write | $0.125 | $2.50 | 20× |
| Output | $0.50 | $10.00 | 20× |

Sources: [Luna model card](https://developers.openai.com/api/docs/models/gpt-6-luna), [Sol 6.1 model card](https://developers.openai.com/api/docs/models/gpt-6.1-sol). These are token rates, not measured costs of solving a task. With identical nonnegative billed token buckets, a positive total cost, and these rates alone, the total ratio lies between 10× and 20×. Different output lengths, attempts, tool charges, context brackets, and service modes can change the actual task-level ratio. No API-equivalent total was calculated because token counts were unavailable.

The separate Codex Standard credit schedule is Luna 2.5/0.25/12.5 versus Sol 6.1 50/2.5/250 credits per million ordinary-input/cache-read/output tokens. It has no separate cache-write charge. These rates do not establish the ratio of included subscription allowance consumption. [Subscription and credit pricing](https://learn.chatgpt.com/docs/pricing).

## 3. Technical pilot and runtime boundary

| Check | Actual observation | Status |
|---|---|---|
| CLI identity/authentication | Installed CLI reports `0.159.0-alpha.3`; login status reports ChatGPT; standard API-key environment variables absent | Observed, without exposing credentials |
| Default App Server initialization | Failed to initialize SQLite state under a read-only runtime directory | Blocked before model execution |
| Ephemeral CLI execution | Requested Luna, `medium`, read-only sandbox, user config ignored; initialization failed on a read-only filesystem | Blocked before model response |
| Writable state/log configuration | App Server given supported SQLite/log directory overrides inside the writable workspace; another read-only dependency remained | Blocked; no permissions bypass or account change |
| Native model probes | Two real subagent calls requested Luna and Sol 6.1, each `medium`, each `fork_turns=none`; both returned the exact required JSON | Passed for answer-only invocation |
| Effective settings | Native tool accepted both requests, but returned no independent attestation of applied model, effort, speed, or model snapshot | Unknown beyond requested settings |
| Fresh review context | E-only received the same task prompt in a fresh requested context, without W answers or reasoning | Requested boundary; platform context not independently exported |
| Protected acceptance | Offline checker rejected an intentionally incorrect required answer; extra positive approval prose/fields cannot override failure | Passed for this output gate |
| Files, restoration, interruption, resume/fork | No model file operation was part of this fixture; separate filesystem isolation, rollback, interruption accounting and session lifecycle were not exercised | Not certified |
| Quota and token telemetry | CLI discovery could not initialize; native completion interface exposed no tokens, cache, quota windows, or billing receipt | Economic measurement blocked |

There were three distinct failed startup configurations and two diagnostic replays, all retained in the operational ledger. They are infrastructure failures, not model-quality failures; resource/billing telemetry for them is unavailable. The alternative native interface advertises a `priority` service tier and offers no speed selector here. It must not be described as a verified Codex Standard run.

The original [first-experiment plan](first-experiment.md) therefore was narrowed explicitly before comparison: answer-only correctness and basic invocation, not a claim of complete architecture feasibility. The economic stage was not entered because the selected economic resource could not be measured.

## 4. Preregistered fixture and limits

The machine-readable [protocol](../experiments/2026-09-30/protocol.json), six task inputs, exact batch prompt, and gold answers were fixed before comparative model calls; their hashes are in the [preregistration manifest](../experiments/2026-09-30/preregistration-sha256.json). Both models received the exact same English prompt. Each used a fresh context request. The prompts prohibited tools, filesystem access, network and delegation. This is an instruction boundary, not proof of an enforced filesystem sandbox; detailed child tool traces were not exported by the interface.

Budget: at most six model starts, at most 300 seconds per start, one initial batch per model, and a reserve of one W repair plus one E takeover if W failed. Allocation: two technical probes, two comparative batches, up to two conditional interventions. E-only was deliberately limited to its first attempt in this narrowed protocol. Total actual model starts: four. No repair or takeover start was needed. Baseline batches overlapped in time; no isolated latency comparison is claimed.

| Task | Fixed requirement | Gold/reference method | Independent audit |
|---|---|---|---|
| T1 | Peak concurrency and earliest peak for half-open intervals, ignoring empty intervals | Count at every interval boundary | Sweep-line deltas |
| T2 | Deduplicated transfers and one-time reversals | Sequential ledger | Independently derive surviving transfers and conservation |
| T3 | Lexicographically smallest dependency ordering | Greedy available-node traversal | Verify globally sorted permutation is legal and therefore minimal |
| T4 | Left join, NULL, counts, sum and HAVING | SQLite query | Separate relational grouping in Python |
| T5 | 0/1 knapsack with value, weight and lexical tie-breaks | Exhaustive enumeration of all 16,384 subsets | Weight-indexed dynamic programming |
| T6 | Quoted CSV, embedded newline, exact sums and half-even rounding | CSV parser and Decimal | Separately derived integer thousandths and integer rounding |

Gold generation preceded model answers. The checker implementation followed the preregistered exact-JSON comparison rule; it was written after the first completion, without changing that rule or the gold. Every returned task was checked and audited (inclusion probability 1). JSON shape, types, duplicate keys and extra fields matter. The independent audit is deterministic and independent of worker reasoning; no LLM judge was used. Tasks and checks were created by the same controller, so requirement interpretation was not independently human-certified.

## 5. Observed outcomes

| Policy | Correct and accepted | Unresolved | Initial batches | Repair / takeover batches | Interpretation |
|---|---:|---:|---:|---:|---|
| W-only | 6/6 | 0/6 | 1 W | 0 | All initial answers passed |
| E-only | 6/6 | 0/6 | 1 E | 0 | All initial answers passed |
| W→E | 6/6 | 0/6 | Same 1 W checkpoint | 0 | No failure triggered E |

All 12 physical task answers matched the fixed gold; no false acceptance was found within these checks. Both technical probes also passed. Rejected mutation-test data are checker tests, not fabricated model failures. The two policy rows sharing W are not independent replications: the physical experiment contains one W batch and one E batch, not three independent policy runs.

For each logical policy, charge its initial W or E work and all applicable verification; for the physical experiment, count the shared W run once. Exact monetary, token and quota totals, including controller research, failed startup attempts and verification overhead, are unavailable. They cannot be omitted from a future full economic comparison merely because this interface did not report them.

## 6. Measurements and uncertainty

| Quantity | W batch | E batch | Meaning |
|---|---|---|---|
| Requested model | `gpt-6-luna` | `gpt-6.1-sol` | Tool request, not provider attestation |
| Requested effort | `medium` | `medium` | No sweep performed |
| Context | Same `prompt.txt`; `fork_turns=none` | Same `prompt.txt`; `fork_turns=none` | No W output supplied to E-only |
| Observed UTC window | 19:41:26–19:43:20 | 19:42:12–19:44:22 | Earliest pre-dispatch clock to post-delivery observation |
| Wall-time upper bound | 114 s | 130 s | Includes controller/dispatch/notification delays, not exact inference time |
| Actual input/cache/output tokens | Unknown | Unknown | Not estimated from characters |
| Actual subscription allowance / cash | Unknown | Unknown | No API-equivalent proxy used |
| Correct yield on fixed fixture | 6/6 | 6/6 | Six synthetic tasks bundled in one call per model |

Both probes fell within the shared observation window 19:39:34–19:41:08 UTC (94-second upper bound per probe). These loose bounds cannot support a speed ranking or per-task latency. The offline checker and audit can be rerun locally; their timings depend on the local host and are not model inference timings.

`K = C_all_eligible / N_independently_correct_accepted` remains uncomputed because the resource numerator is unknown. Accepted-result reliability and correct yield are both 6/6 descriptively for each policy on this fixture; false acceptance is 0 observed, unresolved is 0. These are not population estimates. One batch per model, shared-context tasks, trivial lexical ordering, possible ceiling effects, no repeats and no representative repository work preclude a general quality or cost conclusion. No escalation benefit, retry-versus-consultation benefit, cache savings, filesystem independence, or high reliability was established.

## 7. Reproduce safely and continue

All reusable data, verbatim completion answers, sanitized observation records and offline scripts are in [the experiment directory](../experiments/2026-09-30/). The records are controller transcriptions, not signed provider logs. Synthetic names in the SQL fixture are invented test data. No credentials, account identifiers, internal session IDs, local runtime paths or private transcripts are included.

From the repository root, reproduce checks without a model or network:

```bash
python docs/experiments/2026-09-30/audit.py
python docs/experiments/2026-09-30/verify.py docs/experiments/2026-09-30/luna-answer.json docs/experiments/2026-09-30/sol-answer.json
```

`prepare.py` regenerates the fixed inputs, gold, prompt and their manifest; run it in a copied fixture directory when preserving the published evidence. A future real model rerun must explicitly choose the same requested configurations and submit `prompt.txt`; offline validation is not a substitute for new inference. No automatic paid model runner is provided.

Critical remaining blockers: obtain a working subscription runtime with writable supported state storage; expose task/batch-level usage and effective settings; validate file isolation and session lifecycle; then select representative repository tasks with independently protected tests. The original branch experiment comparing repair, consultation and takeover still requires actual W-failure checkpoints and a separately fixed budget. The reserve was not spent merely to manufacture a difference.

No new paid budget was needed for this narrowed pilot. A switch to paid API would require separate authorization and a concrete capped budget before any call; it would measure API economics, not the currently unknown included-subscription ratio. The present result supports moving to a better-instrumented pilot, not adopting a routing policy on the assumption of a 20× task saving.
