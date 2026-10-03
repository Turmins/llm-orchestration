# First corrected-controller attempt: postmortem

Version: 2026-10-02. The user launched the corrected controller once. This investigation launched no model calls, repeated no run and preserved the real **3/8 consumed, 5 remaining** budget. The attempt remains charged and unusable.

## Observed primary cause and cost

The original project export passed pointer schema, snapshot hashes and summary schema validation. It reports `attempt_not_usable` because `P01-W-a01` has `stderr_diagnostic`. That status is the acceptance gate, not the underlying stderr cause. The original export omitted telemetry errors, stderr categories, error-event counts and timeout/launch-error flags; those missing fields were identified before inspecting supplemental experiment data.

The supplied experiment directory's structured ledger and hash-matching receipts establish the underlying diagnostic: the pinned `codex_models_manager::manager` path logged a model-catalog refresh failure with `request timed out`. This is a catalog discovery timeout; it is not evidence of a disabled host. No ordinary code/configuration cause for the timeout has been proved. [Pinned catalog refresh handling](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/models-manager/src/manager.rs).

| Observation | Value |
|---|---|
| Native process | exit 0; elapsed 17.279606900003273 seconds |
| Controller timeout/interruption; launch error | false; absent |
| Stdout runtime and telemetry | completed; no parser/accounting errors |
| Error events | error 0; turn.failed 0; item.error 0 |
| Usage coverage | reported_complete_stage |
| Incurred input; output | 7675; 22; input plus output 7697 |
| Cached input; cache-write; reasoning output | 1792; 0; 0 |
| Candidate acceptance | JSON object; visible contract failed; independently computed correctness false in original summary |
| Actual model; isolation | unverified; unverified |

Cached input is included in input, not added again. Complete usage and process exit 0 do not make this a clean runtime success. The JSON-object answer's visible-contract failure is a separate result; hidden grading was not fed to the controller or used to select another task. No E takeover or remaining task was dispatched after the runtime gate stopped.

## Implemented diagnostic repair and tests

The confirmed project defect was insufficient diagnostic projection. The new `inspect_export.py` produces a separate safe postmortem sidecar while leaving the frozen controller files, ledger manifest, original export and receipts unchanged. It checks the project pointer and all snapshot hashes, binds the supplied directory through the existing campaign owner hash, verifies the ledger event chain and row/source provenance, and re-parses hash-matching stdout/stderr receipts. It writes only static diagnostic codes, error-event counts, numeric usage/process fields and acceptance flags. Unknown stderr lines remain classified as `unclassified_stderr`; a recognized timeout does not hide other lines. Raw logs, candidate content, messages, account identifiers and private paths are excluded.

The supplemental consumer entry is `poc-exports/cap8-serial-public-toy-v2/diagnostic-latest.json`; its referenced JSON hash must be checked. It is additionally bound to the original summary hash. A changed ledger/pointer during inspection, receipt tampering, unsafe pointer path, wrong directory or invalid event chain stops publication. No runtime diagnostic is downgraded or ignored, and no ledger slot is refunded. The helper does not spawn subprocesses or initialize a ledger.

Six targeted offline regressions passed in normal and optimized Python, zero failures/errors/skips: retained cost/process status and private-data exclusion; receipt tampering with old diagnostic preservation; snapshot corruption and traversal; directory binding and ledger chain; malformed JSONL with retained usage/error counts; unsafe process metadata rejection. A global subprocess guard forbids all subprocesses in these tests. Evidence: `postmortem-validation-2026-10-02.json` and `postmortem-validation-optimized-2026-10-02.json`. PowerShell parser, Python AST, strict JSON, bilingual parity and diff checks passed. The completed 44-test architectural suite was not rerun or rewritten.

## Preserved state and remaining blocker

The safe sidecar was generated automatically from saved receipts, without manual raw-log copying. Ledger, both raw receipts and the original pointer retained their hashes; the original summary remains stopped at **3/8**, with **5** slots remaining. Existing uncommitted files were preserved. Only the diagnostic code/tests, their safe evidence and bilingual report are published to the existing draft PR; no merge or private-log publication was performed.

The model-catalog request timeout remains unresolved. Available evidence does not establish its network/server/configuration cause, the effective live model or tool mode. The next step is supported non-inference catalog/runtime diagnosis in the ordinary authenticated user environment. Do not repeat the model run, ignore stderr, change auth/security/install settings or migrate/reset the bound ledger to obtain more slots. This patch improves diagnosis of the already incurred attempt; it does not assert a repaired live runtime.
