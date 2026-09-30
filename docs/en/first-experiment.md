# First Experiment

Date: 2026-09-30. A proposal accompanying the updated architecture review; no run has been performed or authorized by this document. Task count, monetary/quota budget, and acceptable latency have not yet been specified.

## Configuration and inputs

- One selected Codex CLI/App Server with a pinned version, one authentication method, and Standard speed. The CLI version inspected here is `0.159.0-alpha.3`; recheck the version for the actual fixture.
- Two candidate configurations: W = `gpt-6-luna`, E = `gpt-6.1-sol`. The proposed starting point is one supported `medium` effort per role, without sweeping modes. First verify availability and effectively applied settings. This does not designate optimal models. [Luna card](https://developers.openai.com/api/docs/models/gpt-6-luna), [Sol card](https://developers.openai.com/api/docs/models/gpt-6.1-sol).
- Technical stage: one safe, disposable repository task with predetermined checks and no irreversible external actions. Economic stage: one not-yet-selected representative family of real tasks, original requirements, base snapshots, protected tests, and an independent method of labeling outcomes.
- Before starting, specify budget, time/attempt limits, and takeover/audit reserves; assign stop authority. Do not automatically change the subscription plan or account settings for the pilot.

## A. Technical feasibility

| Check | Sufficient observable evidence |
|---|---|
| W/E launch and control | Requested and effective model/effort/speed; successful completion and controlled interruption |
| Start/resume/fork | Recorded history and its provenance; a fresh reviewer does not receive worker history. A new ID alone is insufficient |
| File state | Separate working copies of one checkpoint; attempts to write outside the assigned scope are blocked; the reviewed candidate snapshot is immutable |
| Interruption | Remaining processes, changes, usage, and effects are accounted for; “interrupted” does not count as rollback |
| Protected acceptance | A deliberately failing required test cannot be overridden by positive worker/reviewer prose |
| Measurement | Every run, including failure/cancellation, has resource-use and artifact records; missing fields are marked unknown |
| Restoration | File manifest, requirements, environment, and selected history policy match; external data are frozen or acknowledged as nonreproducible |

Use a new `thread/start` and a separate environment for verification. In the installed schema, detached review is already deprecated; the online description still refers to a fork. Do not base independence on this feature. Schema inspection is complete; the behavioral checks listed above are not.

## B. Economic comparison

Initial policies on the same sample with identical acceptance:

1. W-only: execution and no more than one evidence-backed repair attempt; then accepted/unresolved.
2. E-only: direct execution and no more than one evidence-backed repair attempt; then accepted/unresolved.
3. W → E: after an unsuccessful mandatory check, immediately transfer the bounded scope to E; one handoff, without a ladder of additional models.

On a limited sample of identical checkpoints after W failure, separately compare **one more W attempt with new evidence**, **one E consultation + one W application**, and **immediate E takeover**. The first two branches have the same predeclared bounded takeover or unresolved outcome if they fail. These are alternatives from one checkpoint, not a sequence containing every action. Common limits, recovery reserve, and the cost of all checks are included in the comparison.

Save checkpoints before initial execution, before intervention after W failure, before candidate acceptance, and after integration. A checkpoint includes files/patch/untracked inputs, history and its inheritance boundary, requirements/tests, environment/tools, configuration, and remaining budget. Forking a conversation does not restore files; a Git snapshot does not clear history.

## Acceptance, measurements, and stopping

Operational accepted and independently established correct are distinct labels. The same mandatory checks apply to every branch, including E. An expert test or invariant is a proposal until its compliance with requirements is verified. A randomly selected portion of accepted results must receive an independent audit with a known inclusion probability; do not spend the entire budget only on failures.

Measure `K = C_all_eligible / N_independently_correct_accepted` (total cost of all eligible tasks divided by the number of independently correct accepted results), accepted-result reliability, correct yield, false acceptance and error severity, coverage/unresolved, total time, rework, and verification/labeling cost. For API usage, measure actual money, ordinary input/cache read/cache write/output/tool fees without double-counting. For subscriptions, measure actual payments, observed quota/credit consumption, windows/reset times, blocking, and correct completions; report API-equivalent cost separately. Account for concurrent account activity and quota-percentage precision.

Stop a branch when a defect repeats without new evidence, advice is misapplied, the local boundary breaks down, limits are exhausted, or the reserve is threatened. Stop the fixture upon isolation/acceptance failure, unaccounted effects, or inability to measure the selected resource. Do not replace stopping with weaker tests.

A small pilot estimates feasibility and preliminary effects; it does not prove high reliability. Sample size depends on budget and required precision; those values are still needed. Add Astra, other effort/speed settings, reviewer-only strengthening, and a separate counterexample mode only for an observed reason. Before promoting a policy, predeclare `R_min`, `Y_min`, `Delta_R`, `L_max`, and `S_min`, and validate on held-out tasks; the business case additionally needs work volume and maintenance cost.
