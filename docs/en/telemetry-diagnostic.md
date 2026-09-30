# Telemetry Diagnostic and Next Experiment Options

Version: 2026-09-30. Outcome: no usable measurable inference route was established in the current cloud environment. No new model calls or paid API requests were made during this diagnostic.

## Exact startup blocker

The earlier description of a read-only runtime was incomplete. Two bounded, fresh App Server startup diagnostics with writable `sqlite_home` and `log_dir` overrides now establish two distinct layers:

1. The SQLite override works: new SQLite files were created in the writable diagnostic directory. The working directory was also writable. The local CLI supports these settings; they are not a mechanism for relocating managed cloud storage. [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
2. Startup then launches `bwrap`. Its child opens `/proc/self` as a directory and attempts `openat(fd, "uid_map", O_RDWR|O_CLOEXEC)`, which returns `-1 EROFS (Read-only file system)`. The child and App Server exit with status 1 before protocol initialization. Both diagnostic runs reproduce this failure.

Thus the remaining problem is a nested sandbox/user-namespace setup restriction at `/proc/self/uid_map`, not choosing the wrong writable project directory. Changing the project folder or SQLite path cannot fix that observed syscall. We did not disable the sandbox, remount anything, modify namespace permissions, escalate access, repurpose the credential home, copy credentials, or inspect saved/hidden sessions. The diagnostic traced startup executable names and filesystem operations, not credential contents or model traffic. Full local traces are excluded from publication; the sanitized factual record is in the [diagnostic evidence](../experiments/2026-09-30/telemetry-diagnostic.json).

## What telemetry exists, and what is actually available here

The installed `0.159.0-alpha.3` generated schema was inspected locally. Its fields include:

| Surface | Schema fields or events | Interpretation |
|---|---|---|
| Thread start response | `model`, `modelProvider`, `reasoningEffort`, `serviceTier` | Resolved thread configuration; retain alongside requested configuration |
| Model rerouting event | `fromModel`, `toModel`, `reason`, `turnId` | Account for a provider-reported model change |
| Thread token usage | `last`, `total`; `inputTokens`, `cachedInputTokens`, `cacheWriteInputTokens`, `outputTokens`, `reasoningOutputTokens`, `totalTokens` | Record actual received fields per turn; never equate schema presence with a populated receipt |
| Account limits | `rateLimits`, `rateLimitsByLimitId` | Window-level consumption, potentially coarse and shared |
| Built-in collaboration tool | Start accepts model/effort; returned records expose task identity, status and text | No usage or effective-model getter is exposed in this session |

The official [App Server documentation](https://learn.chatgpt.com/docs/app-server) describes `thread/tokenUsage/updated`, `model/rerouted`, `account/rateLimits/read`, and `account/usage/read`. Account token summaries and daily buckets cannot attribute one experiment when other activity shares the account. A working server could provide useful provider-reported evidence, not cryptographic proof of physical model execution. Snapshot resolution and missing/rerouted responses would still need explicit handling.

The [subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) describes configuring models and effort; it does not establish a telemetry export for this particular built-in runner. Inspection of the callable tool contracts found no token-usage, effective-model or billing lookup action. Generic App Server features cannot be assumed to exist in this different interface. No unsupported backend endpoint or hidden session was used to fill the gap. The absence is specific to the interface available here, not a claim that OpenAI has no telemetry elsewhere.

## What the existing 6/6 establishes

The two saved response objects each pass all six frozen checks, and the independent offline audit agrees with the gold. Requested configurations and exact prompts are recorded. This supports basic answer-only execution and correctness on these specific inputs.

It does not establish general model equivalence, high accepted-result reliability, relative latency, token efficiency, subscription savings, or verified effective model identity. The six answers are bundled in one response per requested model and are not six independent runs. W→E reuses W and never escalated. There are no actual tokens to retrospectively reconstruct, and the published timing windows remain loose observation bounds. We neither invent token counts nor substitute timings from another run.

## Minimal ways to unblock measurement

| Option | Required change | What it could measure | Current status |
|---|---|---|---|
| Platform supplies an instrumented native runner | Expose per-run resolved model/reroutes, usage categories and completion timing, plus quota snapshots | Real native-run token use; subscription use only to exposed precision | No such callable interface here |
| Platform supports App Server sandbox initialization | Provide a supported runtime where namespace setup works and state directories are writable; retain normal subscription authentication | Thread configuration, usage events and account-limit snapshots | Requires environment/platform support; no local bypass attempted |
| User supplies an authorized working CLI/App Server endpoint | Supported connected runtime using its own normal login; no credential copying | Same events, subject to actual server version and entitlement | No endpoint supplied; not created |
| Separately authorized API micro-experiment | Explicit spend approval and securely configured API access in an approved environment | API response model, usage and API economics; not included-subscription quota | Proposal only; not run |

Before new subscription inference, first verify read-only initialization, model discovery and limits without a model turn. Then require a small predeclared probe to return model/reroute and usage evidence; stop on missing fields. Token counters alone do not establish the included-allowance conversion. Isolate or log concurrent account activity and use window identifiers and resolution-aware intervals for quota comparisons.

## Proposed API budget, not authorization

Proposed approval ceiling: **$2.00 in API charges**, without purchasing credits or changing account settings. This is a conditional estimate for Standard text-only calls, ordinary context, no regional premium and no paid tools. Confirm current rates and enforce the limits before any call. Sources: [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Sol 6.1](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

A bounded design would use eight frozen tasks, each in a separate fresh context. Per task: one initial W and one direct E; reserve at most one W repair and one E takeover from the same failed W checkpoint. Add one telemetry probe per model. This is at most 17 W and 17 E requests, 34 total, including failures and retries. Disable automatic SDK retries; ambiguous failures consume a request slot and their worst-case budget until reconciled.

Limit each fully assembled request to 8,000 input tokens and `max_output_tokens=4000`, including reasoning. Verify the input-token bound with a supported method before dispatch. Cache writes are conservatively priced at the full cache-write rate for all input, without adding ordinary-input billing again:

`C_W_max = (8000*0.125 + 4000*0.50)/1e6 = $0.003`

`C_E_max = (8000*2.50 + 4000*10.00)/1e6 = $0.060`

`C_fixture_max = 17*0.003 + 17*0.060 = $1.071`

The proposed $2.00 ceiling leaves $0.929 unallocated reserve; it does not authorize more requests. These are conditional bounds, not observed spending or an account-wide hard limit. Reserve the full upper bound before each request; stop if receipts, prices or limits cannot be reconciled. Taxes, pre-existing account commitments and unrelated usage are outside this API-call estimate. No purchase is proposed. [Reasoning cost controls](https://developers.openai.com/api/docs/guides/reasoning) cover generated-token limits; incomplete outputs still incur usage and must count as unresolved, not be silently discarded. The 4,000-token cap may itself limit performance and must remain identical and explicit across policies.

## Neutral next task selection

Before any new comparative call, freeze eight cases spanning dependency scheduling with cycles and ties, constrained optimization, SQL NULL/duplicate semantics, ledger reversals, and parsing/rounding edge cases. Require independently implemented reference checks, nontrivial competing solutions, and full acceptance of every mandatory condition. Use no trial model answers to select cases or expected winners. Publish fixtures/hashes first, randomize a recorded execution order, audit every result, and keep every timeout, truncation and failed attempt in denominators. If all cases again saturate, report that result; do not silently replace easy cases after observing model performance.

This is a proposed follow-up design, not an executed second benchmark or a finalized task corpus. The next necessary decision is which measurable runtime to provide. The existing subscription authorization does not authorize the proposed paid API budget.

## Mandatory per-call telemetry gate

**The current path fails this gate. No new economic comparison may start.** Before comparative inference, demonstrate server usage or documented runtime events linked to every call with `task_id`, `strategy`, actual `model_id`, `attempt`, `stage`, `input_tokens`, and `output_tokens`. A requested model or model self-report is insufficient. Record cache-read and cache-write tokens separately when provided; unavailable categories must be `null`/unavailable, never invented zeros.

Preserve safe raw usage fields and their documented event provenance, response/turn linkage, units, and aggregation semantics. Establish whether input totals include cache reads/writes and whether output already includes reasoning; only subtract mutually exclusive included categories and never add reasoning twice. Do not derive this relationship merely from field names. Store both cumulative and per-turn fields when supplied, with reset boundaries to prevent repeated charging. Record model reroutes; stop attribution if the actual model cannot be resolved. Include failed calls, retries, consultations, escalations and all transferred/replayed context. Shared W execution belongs once in physical totals and once in each logical policy using it. No length-based token estimates or synthetic receipts may substitute for missing server data. This schema-level review has not validated live receipt semantics.

## SWE-rebench suitability and container readiness

[SWE-rebench-leaderboard](https://huggingface.co/datasets/nebius/SWE-rebench-leaderboard) is a better next candidate for repository work: its card provides base commits, issue statements, task Docker images and `FAIL_TO_PASS`/`PASS_TO_PASS`. It also contains solution and test patches, which require a separate private grading boundary. The public card says images are prebuilt; this does not verify that every selected image pulls or passes its controls here.

Read-only infrastructure checks found Docker client and server 28.4.0 on Linux x86_64; the daemon reports 5 CPUs and 18,882,699,264 bytes memory, while the workspace has approximately 29.82 GiB free. These observations are not guaranteed benchmark quotas. Harbor and Podman are not installed. No installation, image pull, container creation, test execution or resource purchase was performed. Docker availability does not fix the blocked App Server or authorize mounting credentials into a container. Image sizes, registry access, test resource limits and actual container execution remain unverified.

The proposed [July 2026 Harbor split](https://hub.harborframework.com/datasets/ibragim-badertdinov/swe-rebench-07-2026/latest) did not load through the browser tool; direct HTTP access returned a proxy 403. A metadata request for the Hugging Face revision was likewise blocked on that direct route. **No immutable revision or image digest is confirmed.** Do not run against a floating `latest`. Before selection, record the immutable dataset/Harbor revision, exact instance IDs, base commits, harness revision and per-task image digest. Verify enough eligible instances exist; do not silently substitute another month if the July pool is too small. Newer tasks reduce some exposure risk but do not prove absence of contamination. Exclude examples whose solution/test patches were exposed in the card during this review from the held-out evaluation.

Use SWE-bench Verified only for smoke testing. The [OpenAI audit](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) found contamination evidence and test defects: 59.4% of an audited 138-task difficult subset had material issues, not 59.4% of the entire benchmark. This motivates independent harness checks and cautious labels; it does not prove SWE-rebench is defect-free.

## Calibration, held-out evaluation and grading boundary

Reserve **8–12 calibration tasks**, then a separate **40–60 evaluation tasks**; do not start either until the telemetry gate and infrastructure controls pass. Split by repository/failure family where feasible, remove duplicates and record selection before observing model results. Calibration may tune operational routing globally; freeze policy, limits and task IDs before opening held-out results. Forty to sixty tasks remain a pilot, not proof of high reliability.

Models receive the issue, base checkout and approved pre-existing/public checks only. Never give them gold patches, test patches, hidden test identities, final grader output or solution-bearing hints/history. Keep grading files outside agent-readable mounts; sanitize images and Git history for leaked solution artifacts. An independent controller validates base/gold harness controls in grader-only environments. Gold is an evaluation control, not an agent input. Label broken/flaky infrastructure separately, retaining counts and resource costs with predeclared exclusion rules.

Routing must use only permitted working evidence: public checks, reproducible requirement-derived checks, bounded progress/timeout criteria. Freeze each candidate before running the hidden final grader on an isolated copy. Do not feed its result back into W repair, E takeover or consultation. If a hidden-grader-based routing comparison is explicitly requested later, label it **oracle-routing baseline** and exclude it from deployable-policy conclusions. The first pilot's generic failure-trigger wording must be specialized to this visible gate for SWE tasks.

## Separate SWE pilot budget scenario

The earlier $2 proposal covers only the answer-only micro-experiment; it is **not** a realistic budget commitment for a repository benchmark. For planning, assume Standard API rates, no premium/tools, at most 100,000 cumulative input tokens and 20,000 generated tokens per role trajectory across all calls and context transfers. These limits must be enforced from verified receipts and conservative reservations, with explicit call/time caps; they are not predictions of typical SWE usage.

At the conservative all-input-as-cache-write rates, a W trajectory costs at most `(100000*0.125 + 20000*0.50)/1e6 = $0.0225`; E costs at most `(100000*2.50 + 20000*10.00)/1e6 = $0.45`. Budget up to two W trajectories and two E trajectories per task: initial W, conditional W repair, direct E, conditional E takeover. This gives `$0.945` per task. It excludes consultation as an additional branch; adding one requires a revised budget before execution. Limits exhausted without a valid solution count as unresolved.

| Phase | Tasks | Conditional API upper bound |
|---|---:|---:|
| Calibration | 8–12 | $7.56–$11.34 |
| Separate evaluation | 40–60 | $37.80–$56.70 |
| Combined tasks | 48–72 | $45.36–$68.04 |
| Two telemetry probes, one per model | 2 | $0.4725 |

A possible approval ceiling is **$90 API-only**, leaving reserve above the upper scenario; this is not authorized and no API calls were made. Container compute, storage, transfer, image pulls, human audit, controller overhead, taxes and unrelated account usage need separate estimates/permission and are not hidden inside that number. Subscription execution instead needs an explicit measured quota/time budget after instrumentation; these dollar figures cannot be converted into included subscription consumption. Do not launch the full evaluation automatically after calibration: review measurements, failures, infrastructure costs and the frozen policy first.
