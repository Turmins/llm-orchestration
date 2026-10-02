# Catalog fallback and unresolved P01 visible failure

Version: 2026-10-02. This follow-up reads safe project exports and public pinned sources. It does not reopen private receipts, credentials or session files. New model calls by this investigation: **0**. The user performed the third launch; the charged campaign stays **3/8 consumed, at most 5 remaining**.

## Catalog timeout semantics and network evidence

Source 0.159.2 wraps `/models` transport/download in a five-second deadline. Deadline expiry becomes `RequestTimeout`. The manager catches a refresh error, logs it and returns the current catalog instead of propagating a turn failure. It starts with bundled metadata; a valid identity-bound memory/cache catalog can replace it. If the in-memory identity is inappropriate, `get_remote_models` returns the bundled catalog. With an explicitly supplied model, the OpenAI manager preserves the requested identifier; this is different from fresh metadata availability or verified backend model attribution.

The pinned bundled catalog includes both `gpt-6-luna` and `gpt-6.1-sol` with `tool_mode=code_mode_only`. Tool-mode selection consults model metadata before feature defaults. Thus catalog freshness can affect local metadata, tool-mode configuration and instructions; a discovery timeout does not itself prove incorrect answer content or silent substitution of the requested model. The live catalog/cache choice, effective tool mode and actual backend model were not exported and remain unverified. No user cache/auth files were inspected to fill that gap.

For this saved attempt, the hash-bound sidecar records process exit 0, completed stdout, full usage, zero runtime error events, no controller timeout and exactly one known stderr category: `model_catalog_refresh_request_timeout`. The original controller maps every nonempty stderr to `stderr_diagnostic` and makes it unusable even if the turn completed. For this recognized source path that mapping is an overly broad acceptance policy, not evidence that the native process or turn failed. Discovery failed; the turn completed with reduced assurance. The warning/error and its costs must remain recorded.

Sources: [five-second deadline](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/model-provider/src/models_endpoint.rs), [catalog fallback and explicit model](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/models-manager/src/manager.rs), [bundled metadata](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/models-manager/models.json), [tool-mode selection](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/core/src/tools/mod.rs).

The public [OpenAI status summary](https://status.openai.com/api/v2/summary.json) retrieved during this investigation reported operational status, with its page timestamp 2026-09-29T18:29:41Z. This aggregate, older observation does not establish the state of the user's authenticated catalog route at the failed request. One unauthenticated HEAD of the public ChatGPT root from the executor returned a transport error without an HTTP response in about 0.131 seconds. It used no credentials and made no model request. That executor observation does not diagnose the ordinary user's route, DNS/TLS/proxy/server cause or historical five-second timeout. No authenticated catalog/live-model probe was performed.

## P01 assembly, visible checks and exact missing evidence

The public packet reconstructed from the unchanged frozen task is 853 UTF-8 bytes and includes the instruction, all seven input intervals, visible rule, response format and task ID. Its hash equals the attempt's exported `prompt_sha256`. Controller source writes that same body before reservation and passes its bytes directly to stdin. No incorrect or incomplete prompt assembly is demonstrated. This checks the controller's recorded/transmitted body, not an independent server-side echo.

The visible checker requires the single intervals key, integer pairs, positive lengths, sorted order and nonoverlapping adjacent intervals; touching endpoints are allowed. It intentionally does not establish original coverage or final correctness. Offline cases verify transitive-overlap output and touching endpoints are accepted, while malformed keys, empty intervals, unsorted/overlapping intervals and boolean endpoints are rejected. An empty output list can pass this structural visible check while failing final coverage/correctness. A JSON object alone is not a correct answer.

The saved safe export reports a JSON-object answer and visible failure, but contains neither the hash-bound answer nor per-check failure codes. Consequently the exact failed condition remains unknown; it cannot be inferred from the 22 output tokens or the catalog timeout. Missing evidence: `visible_failure_codes`, or the original hash-bound candidate in an explicitly permitted safe artifact. Private candidate/stdout files were not read in this follow-up.

The postmortem producer now supports static P01 failure codes without exporting keys, interval values or raw answer text. The next ordinary-user, non-inference producer action is to regenerate its safe sidecar from the already saved experiment receipts, then inspect the exported codes. That producer action was not executed against private receipts in this follow-up. Until the safe codes are supplied, the exact visible failure is a remaining blocker.

From the project root in the ordinary user terminal:

```powershell
py -3 -B -X utf8 .\docs\experiments\toy-poc-v1\inspect_export.py --data-dir (Join-Path (Split-Path (Get-Location).Path -Parent) 'LLM-PoC-cap8')
```

## Implemented assessment, verification and preserved charges

The minimal implemented correction is semantic diagnosis: `inspect_export.py --public-only` reads only the original project export and hash-bound diagnostic sidecar. It recognizes the precise pinned discovery timeout only alongside completed stdout, exit 0, full usage, zero error events and no interruption/tool violation. It reports `completed_with_nonfatal_discovery_warning` and `reduced_catalog_freshness_unverified`; unknown stderr, runtime errors, tool violations or partial telemetry remain blocking/unclassified. It writes `poc-exports/cap8-serial-public-toy-v2/assessment-latest.json`, preserving all source bindings. It does not change the ledger's recorded usable flag, blanket live-routing gate or frozen source manifest, and does not resume the campaign. This is a diagnostic classification repair, not a claimed live-gate repair or clean model success.

Ten targeted diagnostic tests pass in normal and optimized Python, zero failures/errors/skips. They extend the previous six-test suite with public-only/no-private-reader behavior, missing-code compatibility, unknown/error blocking, stale binding rejection and P01 rule cases. Counts are not added: the previous architectural suite has 44 tests; the first postmortem evidence has 6; this extended diagnostic suite has 10 including those 6. The 44-test suite was not rerun. Evidence: `discovery-validation-2026-10-02.json` and `discovery-validation-optimized-2026-10-02.json`. Python AST, JSON, PowerShell parser, bilingual parity, source provenance and diff checks pass.

| Charged attempt | Input | Cached input | Cache-write | Output | Reasoning output | Recorded diagnostic |
|---|---:|---:|---:|---:|---:|---|
| Historical W | 7629 | 1792 | 0 | 90 | 66 | Code Mode host unavailable; exit unknown |
| Historical E | 8319 | 0 | 0 | 68 | 44 | Code Mode host unavailable; exit 0 |
| User-run P01-W-a01 | 7675 | 1792 | 0 | 22 | 0 | Catalog refresh timeout; exit 0; visible failure |

Known input/output subtotals are 23623/180; their sum 23803 is a known subtotal, not a claim of complete telemetry across the historical partial receipts. Cache/reasoning components are not added again. Monetary/API charge and actual model remain unknown. No refund, relaunch, E takeover, task reselection, security/auth/install change, raw-log publication or merge was performed. The exact P01 failure and live catalog/network cause remain unresolved; changing the bound live policy is deferred until those facts and reduced-assurance behavior are reviewable.
