# Economic Experiment: Four-Task PoC and Optional Future Protocol

Historical protocol. The active controller uses the bounded small plan described in [verified controller fixes](controller-audit-fixes-2026-10-01.md); earlier comparison budgets and launch instructions below do not authorize current inference.

Latest control: [preparation-only checkpoint](preparation-checkpoint.md). Execution is paused; no new runtime/model probes are authorized by this preparation.

## Current stage — subscription-only four-task PoC

Updated 2026-10-01. **Only the existing subscription is permitted. Paid API is neither the current path nor a fallback.** The current objective is per-task, per-model input/output and available cache token measurements, including every attempt and transfer. Token use is not automatically included-allowance consumption. The 10+50 design below is an optional later stage; its historical $110 estimate is not a current recommendation or authorization.

Current runnable materials: [plan](../experiments/toy-poc-v1/plan.json), [four frozen original tasks](../experiments/toy-poc-v1/tasks.json), [offline harness](../experiments/toy-poc-v1/harness.py), [MIT license](../experiments/toy-poc-v1/LICENSE), [synthetic-only report](../experiments/toy-poc-v1/synthetic_report.json). These are original toy tasks, **not SWE-rebench or another benchmark**. No dataset metadata retrieval is needed for this PoC. The task set and order are fixed before any model result; no replacement to manufacture W failures is allowed.

| ID | Small objective task | Visible routing signal | Separate final acceptance |
|---|---|---|---|
| P01 | Strict-overlap interval union | JSON shape, order, positive lengths, non-overlap | Exact union and endpoint semantics |
| P02 | Idempotent transfer ledger | JSON shape, integer balances, conserved total | Exact balances after all events |
| P03 | Directed shortest path | Valid simple path and correctly summed cost | Minimum cost and lexical tie-break |
| P04 | Small 0/1 packing | Valid unique IDs, sums and capacity | Optimal value, weight and lexical tie-break |

All requirements, including optimality, are given to both models. Hidden means the reference calculation/result is withheld, not that requirements are secret. Four independently worked reference answers were checked against the algorithmic grader. The independent acceptance is controller code, never model prose. The grader and references are present in the public harness for reproducibility, so agents must receive only exported packets in a separate environment with no repository/grader access or network tools. Packet filtering passes offline tests; live filesystem/tool isolation remains a gate, not an established fact. Do not deploy this harness in an agent-readable checkout and call the grading hidden.

**Policies:** W requests `gpt-6-luna`; E requests `gpt-6.1-sol`; both request `medium` and Standard, subject to actual runtime confirmation. On each task, W→E gets one W call and at most one fresh E takeover. E-only gets one independent E call with the original task only. No repair loops, consultation or retries. Alternate which baseline is dispatched first by task index, execute serially, and record monotonic dispatch/completion timestamps when available. Both policies use the same task requirements and final grader.

**Routing:** check authoritative usage/model attribution and runtime health first. A missing receipt, model mismatch, infrastructure failure, unaccounted cancellation or limit violation stops the experiment; it does not trigger E. Otherwise JSON parse/schema or frozen visible-invariant failure triggers one takeover. A visible pass freezes the candidate even if final acceptance later fails. Send E only the original packet, W candidate and visible failure evidence; its full repeated context is part of E input usage. Freeze all comparative candidates and their byte hashes before controller-only final grading. No hidden grader output may feed routing. If W has no visible failures, zero natural handoffs is a valid result; report it without selecting replacement tasks.

**Separate technical handoff:** a forced W→E transfer on P03 may test packet/lifecycle mechanics even if W passes. Give it its own experiment identity and ledger, label it forced, and exclude it from economic/token-efficiency conclusions. At most two calls are reserved for this technical case. No real forced handoff has been run. Synthetic failure injection tests procedure only and is never evidence of a model error or savings.

**Small planned limits:** four tasks; at most 12 comparative calls (4 W, 4 E-only, up to 4 takeovers), plus at most 2 telemetry probes and 2 separate technical calls: 16 overall. One call per attempt, automatic retries disabled. Proposed per-call caps: 4,000 total input tokens including platform/transfer context, 2,000 generated tokens including reasoning, 120 seconds. These are not observed usage. A supported subscription runtime must make the bounds enforceable before dispatch; reject oversized packets and reserve the next call's maximum. Stop at included-subscription limits without buying credits or enabling overages. No new credentials, installations, security changes or sandbox bypasses are allowed.

**Reuse existing telemetry:** the harness imports the existing schema/accounting module. The receipt validator requires subscription billing, all four matched task pairs, exactly one W initial and E baseline per task, at most one linked E takeover, and the frozen requested/confirmed model checks. It rejects probes/forced-technical logs mixed into comparison records. Required `task_id`, actual model, input/output, stage/attempt/request linkage and safe raw usage provenance remain unchanged. Cache unavailable stays null. The validator produces overall and per-task token totals, not money or an inferred quota ratio. It is a consistency checker, not proof of server authenticity; the supported collector and source semantics must be verified independently. No live collector is available here.

Offline commands, using the already available dependencies:

```bash
PYTHONDONTWRITEBYTECODE=1 python docs/experiments/toy-poc-v1/harness.py synthetic
PYTHONDONTWRITEBYTECODE=1 python docs/experiments/toy-poc-v1/harness.py prepare --out /tmp/toy-poc-agent-packets
```

The export directory must not already exist. The harness also offers visible-only `route` and `handoff`, controller-only `grade` requiring the pre-frozen candidate SHA-256, and `validate-usage` for later externally collected receipts. It contains **no model dispatcher or paid API path**. Missing candidate files are infrastructure errors; malformed candidate JSON is visible evidence. No untrusted model code is executed. The synthetic report uses identical invented token counters for W and E to avoid suggesting a winner; it does not replace real calls.

**Observed now:** a bounded App Server initialization, without a model turn, again exited 1 with a read-only error and no initialization response. CLI `0.159.0-alpha.3` reports ChatGPT login, which does not establish a working measurable runner. New real model calls: 0; token/allowance comparison: not performed. The prior sandbox diagnosis remains unresolved and was not bypassed. The Windows information below is user-reported history, not work performed on the local PC during this PoC.

**Minimal next step:** provide a supported, already-authorized cloud subscription runtime exposing actual model identity and task-attributed server input/output usage, with safe raw receipts, optional cache counters and enforceable tool/context boundaries. It must initialize normally and support the frozen caps without new payments. Then the first bounded probe can test the actual receipt contract; only a successful gate permits the four-task comparison. Until that change, stop after offline preparation rather than repeating unmeasurable calls.

## One explicitly requested runtime smoke-test — 2026-10-01

This is a separate startup smoke-test, not an economic comparison or a repeat of the four-task PoC. Exactly one runtime start was attempted with the installed CLI `0.159.0-alpha.3`, using the unchanged configuration:

```bash
codex app-server --stdio
```

It exited with code 1 before protocol initialization and before an account query or model turn. Stderr reported `Read-only file system (os error 30)` and `failed to initialize sqlite state runtime`; the latter identified the managed runtime home. The full repeated runtime-home path is omitted from this public report. No sandbox/security/auth configuration, credentials or installation was changed. No second startup, alternative runner, container, paid API or local PC was used.

| Observation | Result |
|---|---|
| Stage | Startup: SQLite state initialization |
| Runtime starts in this smoke-test | 1 |
| Model calls dispatched | 0 |
| Intended model if startup/auth succeeded | `gpt-6-luna` |
| Requested model actually sent / confirmed actual model | `null` / `null` |
| Input / output / cache-read / cache-write tokens | `null` / `null` / `null` / `null` |
| Usage source / inference scope | `unavailable` / `unavailable` |
| Subscription authorization via running server | Not reached |

These nulls mean unavailable telemetry, not zero consumption. No arithmetic answer was generated. The verified blocker is the installed runtime's startup failure; token comparison remains unperformed. The minimum next step is a platform-supported subscription runtime that initializes normally and exposes authenticated model and per-call usage events. Stop here; the result does not authorize a workaround or recurring tests.

## Optional future protocol — not the current plan

The retained sections below document the earlier larger proposal. Their financial scenarios are historical and do not create a paid fallback for the subscription-only PoC.

Version: 2026-09-30. This is a reviewable plan and offline validation package, not authorization or evidence of a new benchmark run. No model calls, API spending, infrastructure installation or container starts were performed for this preparation. Work stayed in the cloud workspace.

## 1. Status and deliverables

The [machine-readable protocol](../experiments/economic-protocol-v1/protocol.json) freezes the proposed policies, selection seed, limits and budget. The [manifest](../experiments/economic-protocol-v1/manifest.json) is `INCOMPLETE_METADATA_UNAVAILABLE`, with `runnable=false`, empty task lists and null revisions. The official [dataset metadata API](https://huggingface.co/api/datasets/nebius/SWE-rebench-leaderboard), [commit page](https://huggingface.co/datasets/nebius/SWE-rebench-leaderboard/commits/main) and [July Harbor page](https://hub.harborframework.com/datasets/ibragim-badertdinov/swe-rebench-07-2026/latest) were unavailable through the browser tool in this preparation. No dataset rows or patches were fetched. Actual duplicate checks, split separation and image-digest verification therefore remain pending.

Cloud blockers remain those in the [telemetry diagnostic](telemetry-diagnostic.md). The user separately reports a Windows checkout and working App Server `0.159.2`, but the isolated `CodexSandboxOffline` cannot see an account and reports daemon error `10050`. This is user-supplied information; no Windows files were read from this cloud environment and no local PC was used. It does not supply an authorized runtime.

The [usage schema](../experiments/economic-protocol-v1/usage.schema.json), [offline arithmetic validator](../experiments/economic-protocol-v1/accounting.py), [metadata-only selector](../experiments/economic-protocol-v1/select_metadata.py) and [synthetic tests](../experiments/economic-protocol-v1/test_preparation.py) are small preparation utilities. They neither launch models nor orchestrate containers. The prior 6/6 remains correctness on six specific bundled inputs, not a token, quota, timing or general-capability measurement.

## 2. Measurement gates

| Gate | Requirement before comparative execution | Current state |
|---|---|---|
| Authorization | Explicit cloud runtime access, selected billing mode and approved quota/time or API/compute budget | Missing; preparation only |
| Identity and attribution | Every billable call linked to task, policy, stage, attempt and server request; provider/runtime-confirmed model | Missing |
| Required counters | Authoritative input/output tokens for every call, including failures; validated source semantics | Missing |
| Resource objective | API charge reconciliation or attributable subscription quota windows with precision and concurrent activity recorded | Missing |
| Dataset | Immutable revisions, deterministic task IDs, duplicate audit and disjoint calibration/eval groups | Missing |
| Isolation and acceptance | Working isolated agent/grader environments, private hidden tests, immutable candidates, base/gold controls | Not executed |
| Phase transition | Review calibration measurements and freeze policy before held-out evaluation | Not reached |

A missing required receipt stops the whole economic comparison, not just that row. Preserve the failed/missing record and worst-case reserved budget; do not quietly drop it from denominators. Unknown cache fields do not invalidate known inclusive input/output counts, but prevent exact tariff reconstruction when differently priced buckets cannot be separated. Independent authoritative total charges may still support API-money accounting; missing subscription attribution still blocks subscription savings claims. A probe must be separately bounded and authorized after supported initialization/discovery; no probe is authorized by this preparation.

## 3. Per-call journal contract

Every property in the schema is present. Unavailable values are null with an availability note; zero is allowed only when the source actually reports zero. Store safe source receipts privately with access controls. Public examples here are explicitly synthetic. Pseudonymize server/session identifiers for publication while retaining a private auditable mapping; never include credentials, signed URLs, prompts, hidden tests or reasoning text in the usage evidence.

| Field group | Contract |
|---|---|
| Identity | `experiment_id`, `task_id`, `record_id`, `physical_call_id`, `split` identify the experiment, task, receipt and actual invocation |
| Policy | `strategy`, `logical_strategies`, `stage`, `attempt`, `parent_call_id` distinguish initial work, repair, takeover, consultation/application and shared work |
| Runtime linkage | `request_id`, `response_id`, `thread_id`, `turn_id`, `event_ids`, `reset_boundary_id` preserve source linkage without merging unrelated calls |
| Model/configuration | Requested and confirmed model, effort and speed are separate; `model_evidence_ref` and `rerouted` provide provenance |
| Usage | `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `reasoning_output_tokens`, `total_tokens` retain source values |
| Semantics | `input_semantics`, `output_semantics`, `cache_categories_disjoint`, `scope`, `billable_calls_in_scope`, `source_contract_ref` specify what counters mean |
| Safe raw evidence | `raw_usage`, `raw_usage_sha256`, `usage_field_paths` preserve the numeric source tree, its canonical hash and JSON Pointer mapping to each copied counter |
| Completion | `status`, `receipt_status`, nullable UTC timestamps and elapsed seconds distinguish completion, failure, cancellation and missing evidence |
| Billing | `billing_mode`, `actual_api_charge_usd`, `charge_evidence_ref`, `quota_window_id`, `quota_delta`, `quota_precision`, `tools_charge_usd` separate dollars and quota |

Only server usage or documented runtime events qualify. The validator rejects a synthetic row in real mode, missing input/output or confirmed model, provisional receipts, account/thread scope, and a turn containing more than one billable call. A runtime turn is not automatically an inference call. Cumulative snapshots must be retained but are not accepted as per-call receipts by this utility; a separately verified adapter is needed if the runtime exposes only cumulative data. An event name alone does not establish scope.

Pin requested model IDs to the confirmed IDs during future discovery. The current validator deliberately stops on model mismatch or rerouting instead of silently treating a requested alias as proof. Legitimate alias-to-snapshot mapping would require a documented, frozen adapter amendment. The schema and local hashes establish consistency, not authenticity: an authorized collector must verify provenance and field semantics against live events. See [App Server events](https://learn.chatgpt.com/docs/app-server).

## 4. Summation and cost rules

Use exactly one final receipt per physical call. Identical replays count once; conflicting final records or reassigning one server request to two physical calls are errors. Every attempted request, including transport failures, must have a ledger row. Automatic transport retries are disabled; an ambiguous failure pauses the fixture until usage is reconciled, rather than granting a free retry.

For inclusive input with documented mutually exclusive cache categories:

`I_uncached = I_input - I_cache_read - I_cache_write`

For input reported without cache categories:

`I_total = I_input + I_cache_read + I_cache_write`

If either necessary cache quantity is unavailable, do not substitute zero or infer an ordinary-input bill. Reject negative residuals or categories exceeding totals. Unknown/non-disjoint cache semantics prevent bucket pricing. For output that already includes reasoning, use the reported output once. Only a documented exclusive output definition permits:

`O_total = O_visible + O_reasoning`

Where the source total follows the same inclusive convention, validate `T_total = I_total + O_total`. The raw field mapping is checked for equality before arithmetic. Do not guess these relationships from names; the collector must establish them in a versioned source contract before measurement.

`C_API_tokens = (I_uncached*p_input + I_cache_read*p_read + I_cache_write*p_write + O_total*p_output)/1e6`

This expression is a tariff calculation, not proof of actual payment. Add separately evidenced tool/other charges once, reconcile against actual charge records, and do not add cache-write pricing to ordinary pricing for the same tokens. Keep API-equivalent sensitivity estimates separate from subscription usage. Include all repeated context, transfers, repairs, consultations and unsuccessful work, plus separately recorded checking/compute/controller costs. Shared initial W counts once physically and once in each logical policy that uses it; report both views and shared-sample dependence. The offline utility aggregates tokens only, not a complete bill or quota ledger.

## 5. Fixed policies and visible routing

W requests GPT-6 Luna and E requests GPT-6.1 Sol, each with `medium` and Standard speed, subject to future confirmation. Each policy gets at most two trajectories per task. A trajectory is a bounded sequence of server calls, not one API call.

| Policy | Initial work | Single permitted intervention |
|---|---|---|
| W-only | W from clean base | One W repair using visible failure evidence |
| E-only | E from clean base, no W result | One E repair using visible failure evidence |
| W→E | The same initial W checkpoint as W-only | One fresh E takeover with scoped candidate diff and visible failure evidence |

Before any model work, freeze permitted file scope and public check commands; verify those checks pass on the base. Commands and their hashes are part of each task's future manifest. The visible gate has deterministic precedence:

1. Infrastructure, telemetry, scope or snapshot integrity failure, or invalid base checks: stop the task/fixture as appropriate; do not escalate a model.
2. Frozen public checks do not finish within the check limit: unresolved, without a model intervention.
3. Candidate exists and every frozen public check passes without a regression: freeze an operational candidate. Hidden acceptance may later reject it.
4. Candidate is absent or a frozen public check regresses versus base, with all preceding preconditions satisfied: permit exactly one evidence-backed repair or takeover if only the initial trajectory has been used. Otherwise unresolved.

A model timeout does not itself cause escalation. First stop and reconcile processes/usage, recover the candidate snapshot and run the visible gate; if that cannot be done, stop without intervention. No repeating attempts, consultation branch, extra expert or hidden-result-triggered intervention is included. Consultation/application stages exist in the ledger for completeness, but enabling them requires a new preregistered policy and budget. Fresh E receives original requirements, candidate files/diff and visible evidence only, not worker reasoning or hidden results. Save requirements, base/candidate hashes, command set, environment, history policy and remaining budget at each handoff.

## 6. Independent hidden acceptance

Keep gold patches, test patches, hidden test identities and grader output inaccessible to agents and the router. Run final grading only after all policy candidates for the phase are frozen. Use isolated grader copies, pinned images/harness and the complete required `FAIL_TO_PASS` and `PASS_TO_PASS` checks. Verify base/gold harness controls in the grader boundary; they are not agent inputs. Audit all results and classify infrastructure defects separately under rules fixed before observing model success. Do not turn operational success into correctness by model prose.

The final grader never triggers repair or takeover. Any later hidden-grader routing experiment must be separately named `oracle-routing baseline`; it is disabled here. Report accepted-result reliability, independently correct yield, false acceptance, unresolved, costs and coverage over all eligible tasks. If no independently correct accepted result exists, cost per such result is undefined, not zero:

`K = C_all_eligible / N_independently_correct_accepted`

## 7. Metadata-only deterministic sampling

Use [SWE-rebench-leaderboard](https://huggingface.co/datasets/nebius/SWE-rebench-leaderboard), provisionally the July 2026 Harbor edition, only after immutable provenance is supplied. The target is **10 calibration and 50 eval tasks** within the requested ranges. Seed: `llm-orchestration/swe-rebench-2026-07/v1/20260930`. Do not change the seed, month or counts after seeing pools or outcomes; insufficient eligible data requires a recorded amendment before any run.

The selector accepts only an authorized metadata export with immutable dataset/Harbor/harness revisions and rows containing exact instance ID, canonical repository and repository-family group, base commit, creation date, issue key, problem-content fingerprint, image reference/digest and repository license. It rejects extra fields, including patches or full issue text. A trusted metadata preparer must derive/verify fingerprints without giving solutions to the selector or agents. Revisions, groups, licenses and digest provenance still require verification; string validation is not remote verification.

Deduplicate identical IDs; reject conflicting IDs. Collapse connected duplicate groups sharing a problem fingerprint or repository/issue key, retaining the lexicographically smallest ID. If any member is a previously exposed example, exclude the entire group. Retain a reasoned exclusion ledger. Restrict to the pinned July month. Repository families, including known forks, must be curated consistently before hashing.

Assign repository groups by the first 8 bytes of SHA-256 of seed, NUL, the literal group marker, NUL, and case-folded group name, modulo 5. Bucket 0 is calibration; other buckets are eval. Within each pool rank SHA-256 of seed, NUL, the task marker, NUL, and exact instance ID; use ID as the tie-breaker. Take 10 and 50 respectively. This makes selection independent of input order and keeps repository groups disjoint. Check ID/fingerprint duplication and split overlap before freeze. The selector always emits a non-runnable manifest: actual image verification, telemetry, permissions and resource gates remain external.

Publish only allowed IDs, hashes, source links and metadata with attribution; never dataset contents or solution/test patches. The dataset card identifies CC-BY-4.0, with individual repository licenses to check. Preserve attribution to Nebius/SWE-rebench authors. SWE-bench Verified remains smoke-test only, following the [OpenAI audit](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/); freshness does not certify contamination-free evaluation.

## 8. Planned limits and revised budget

All values here are **plans**, not observed usage. Per trajectory: at most 20 server calls, 1,800 elapsed seconds, 100,000 cumulative input tokens including replay/transfer, and 20,000 generated tokens including reasoning. Public checks: 300 seconds; hidden checks: 6,000 seconds, subject to a task's tighter frozen limit. Pre-reserve the full next-call upper bound and stop before exceeding a trajectory or experiment limit. Cancellation is not rollback and does not erase incurred usage.

The earlier $90 scenario allowed no E-only repair. This protocol restores one E repair and therefore budgets at most two W plus three E trajectories per physical task. At the previously dated conservative API tariffs (all input priced as cache writes), the conditional bounds are:

`C_task_max = 2*0.0225 + 3*0.45 = $1.395`

| Planned allocation | Conditional API bound |
|---|---:|
| 10 calibration tasks | $13.95 |
| 50 separate eval tasks | $69.75 |
| One future telemetry probe per model | $0.4725 |
| Total | $84.1725 |
| Proposed approval ceiling, API only | $110 |

Rates and assumptions must be revalidated before authorization. No API spending is authorized. Infrastructure, storage, transfer, checking, human/controller costs and taxes require separate budgets. Subscription quota/time budgets remain null until the authorized runtime supplies usable evidence; these dollar bounds cannot be converted to included quota. Review calibration before separately allowing eval; neither phase starts automatically.

## 9. Offline checks and remaining work

Run in the existing cloud environment, which already has the required JSON Schema validator:

```bash
PYTHONDONTWRITEBYTECODE=1 python docs/experiments/economic-protocol-v1/test_preparation.py
```

The tests generate unmistakably synthetic receipts and metadata in memory. They check schema validity, provenance-field consistency, missing fields, cache/reasoning arithmetic, replay/conflict handling, failed-call inclusion, shared-work allocation, routing precedence, deterministic sampling, duplicates and incomplete manifests. They are not model results or evidence that any runtime emits the required fields. No dependency installation is performed. On a future host lacking the validator, report that dependency rather than silently installing it.

Remaining gates: authoritative metadata/revisions; real duplicate/split/digest audit; approved cloud runtime and billing mode; authenticated model/call/input/output evidence with validated semantics; isolated hidden grader; approved resource budgets; and calibration review. User-reported Windows diagnostics do not close them. This preparation stops after publication; waiting for telemetry is not permission for additional experiments.
