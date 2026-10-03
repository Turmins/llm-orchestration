# Controller fixes after the independent architecture audit

Version: 2026-10-01. Scope: project code and offline verification. New inference launches: **0**. The real PoC budget remains **2/8 consumed, at most 6 remaining**. This report supersedes the historical cap8 and continuation launch instructions; those documents and evidence are preserved.

## 1. Result and evidence level

The active standard-library controller now implements a serial W → public checks → optional one E takeover. Durable accounting, recovery and automatic project export are implemented and exercised with synthetic fixtures. This is independent deterministic grading of public toy tasks. It is not evidence of a successful model run, unseen-task secrecy, authoritative backend identity, measured subscription quota or economic savings.

The factual starting checkout was HEAD `94b50f9b06aca06bcdfdb12a631923f5d79eef14`, with existing runner/ledger repairs and uncommitted reports. No reset, clean, stash or pull was used. A copy of the existing editable code/index was verified before modification. Existing audit, runtime evidence and historical reports were retained. A temporary executor disconnection interrupted the first attempt; after reconnection, commands worked and the proposed plan/backup were confirmed absent before creating them.

The implementation follows `docs/ru/architecture-audit-2026-10-01.md` and `docs/en/architecture-audit-2026-10-01.md`. Local checkout instructions contained no applicable AGENTS file or local skills directory. The bilingual reporting convention was followed. OpenAI Docs was used for official configuration guidance; CLI behavior is attributed to the pinned source rather than a moving branch.

## 2. Implemented changes and reasons

| Finding | Implemented behavior | Reason and limit |
|---|---|---|
| A4, A6 | A project campaign lock and directory binding plus a private OS lock protect one hash-chained ledger. Prompt bytes and a durable reservation precede spawn. Updates use flush, fsync and same-directory atomic replacement. | Concurrent controllers, another data-dir and a missing bound ledger cannot silently obtain a fresh cap8 budget. This is a local file controller, with no service or queue. |
| A4, A6 | Legacy W/E evidence is imported once. Reservations remain charged until a recorded observation is available; unknown attempts cannot relaunch. Resume validates manifest, source and artifact hashes. | Crash after reservation is conservatively charged. Available stdout and process metadata can reconstruct a lost terminal record; unknown exits remain blocked. A corrupted ledger is never reset. |
| A5, A8 | JSONL is parsed line by line with byte offsets, line/source/receipt hashes and retained usage observations. Identical receipts count once; conflicts preserve observations and a minimum known lower bound. | Malformed tails, invalid UTF-8, partial receipts and error events no longer erase earlier numeric usage. Conflicting or incomplete coverage blocks continuation. |
| A1, A5 | Runtime, safety, usage coverage, visible decision and independent correctness are distinct fields. Unknown JSON diagnostics and nonempty stderr fail closed. | An exit-zero startup capability warning can retain a complete numeric receipt and a correct candidate while remaining unusable. Historical failures never become clean successes. |
| A2, A9 | One W per planned task, then one E only on a public JSON/schema/invariant failure with usable runtime and usage. No baseline, repair, forced handoff or automatic retry. | The final grader is invoked only after collection stops; hidden-only errors cannot route another attempt. Earlier frozen results survive a later failure. |
| A1, A7 | Conflicting Code Mode selector/host overrides were removed. Read-only sandbox, no escalation, tool restrictions, disabled web and isolation from arbitrary user configuration remain. | Native tool-mode selection is preserved. Host availability and effective mode remain unverified; preserving the supported host does not justify broader permissions. |
| A3, A9 | Immutable allowlisted JSON/RU/EN snapshots are written automatically under the project, with an atomic final pointer and hashes. | Exports exclude candidate content, raw logs, reasoning, diagnostic messages, credentials, identities, environment/config dumps and absolute private paths. The dot can consume the files through project access. |
| A10 | UTF-8 byte transport, native argv arrays and LF source policy are explicit. Working-tree, LF and historical Git-blob hashes are separately named. | Original receipts are not normalized before hashing; reconstructed historical candidate hashes are not presented as hashes of original private evidence. |

The journal is an atomically replaced JSON snapshot of an append-only event chain. This small cap8 implementation avoids partial journal tails without introducing a database or general workflow framework. OS-crash tests cover the reservation window; power-loss durability of a particular disk/filesystem is not established.

Preflight requires CLI version 0.159.2 and the audited executable SHA-256 `34549ded6e2aee87c911c62d025e52e26c488683d0f489cd68f756baef1a6df6`. A mismatch stops before executing the binary; an update needs a separate adapter review.

## 3. Fixed small test and historical accounting

The new [frozen plan](../experiments/toy-poc-v1/small-test-plan.json) selects the original tasks **P01–P03**, in that order, before any new inference. P04 is explicitly excluded from this small test and appears in every report. No task replacement based on outcomes is permitted. The maximum future envelope is **3 W + 3 E = 6 new launches**, plus the two historical launches, within cap8. If no natural takeover occurs, report zero; do not spend a new call to manufacture one. Requested models remain `gpt-6-luna` and `gpt-6.1-sol`, with medium effort and default speed. Actual model identity remains unknown.

| Historical user-supplied quantity | W | E | Known subtotal |
|---|---|---|---|
| Input | 7629 | 8319 | 15948 |
| Cached input | 1792 | 0 | 1792 |
| Cache write | 0 | 0 | 0 |
| Output | 90 | 68 | 158 |
| Reasoning output | 66 | 44 | 110 |
| Process exit | unknown | 0 | — |
| Elapsed seconds | unknown | 7.1023351 | — |

Input plus output is **16106**. Cached/reasoning components are not added again. Both rows retain the Code Mode startup capability failure, user-supplied provenance and unavailable original raw hashes. Optional counters remain null when absent; null values do not cause arithmetic exceptions. The historical arithmetic smoke is outside this budget and is not imported.

## 4. Offline verification

The final regression suite contains **41 tests**. Both normal Python and optimization mode pass with **0 failures, 0 errors, 0 skips**. PowerShell parsing returns **0 errors**; Python AST, strict JSON and git diff checks pass. See [normal evidence](../experiments/toy-poc-v1/offline-validation-2026-10-01.json) and [optimized evidence](../experiments/toy-poc-v1/offline-validation-optimized-2026-10-01.json), which include source representation hashes and test counts. The verifier blocks unexpected subprocess executables before spawn.

Coverage includes corrupted JSONL after valid usage; completed receipts with runtime errors; partial/missing/zero/invalid counters; duplicate and conflicting receipts; reservation-write failure; process crash after reservation; recovery after terminal-append failure; duplicate invocation; resume accounting; two real local Python processes competing for the OS lock; changed data-dir and missing/corrupted ledger; provenance and reconstructed evidence; no hidden routing; bounded takeover and final E failure; poisoned candidate data; candidate/receipt tampering; export allowlists, counters, atomic pointer failure, traversal and Windows junction rejection; native Windows argv; UTF-8/BOM/CRLF; JSON and bilingual report parity.

Run/export paths were tested through synthetic captures. The optional project demo export is explicitly marked `SYNTHETIC_FIXTURES`; its invented launches/counters do not change the real 2/8 budget and do not prove model success. No Codex inference executable was spawned during verification.

## 5. Entry point, resume and export contract

Use one persistent private directory outside the checkout and outside automatically cleaned temporary storage. Keep it for every restart; do not choose another directory to bypass the budget. The project stores only its directory hash in ignored campaign metadata. Raw prompts/stdout/stderr/process receipts and the authoritative ledger stay private, separate from stage workspaces. Each stage workspace contains only its public packet. A directory hash and prompt separation are not read-secrecy boundaries.

For offline verification from the controller directory:

```powershell
python -B -X utf8 verify_offline.py --out offline-validation-2026-10-01.json --demo-export
python -B -O -X utf8 verify_offline.py --out offline-validation-optimized-2026-10-01.json
```

After choosing `$PrivateData`, this command only reconstructs/exports accounting and does not call the runtime:

```powershell
& .\docs\experiments\toy-poc-v1\run-poc.ps1 -DataDir $PrivateData -ExportOnly
```

Omitting both Run and ExportOnly performs version/help/login-method/feature-name preflight, with no inference. A future explicitly authorized run additionally requires `-Run -RuntimeReviewed -AcceptUnverifiedModelAndIsolation` and the existing native executable through CodexExe. RuntimeReviewed is a caller attestation of prior compatible-runtime verification, not a host installation or an automatic safety proof. The old `--cap8` and `--forced-handoff-only` switches are removed. Resume uses the same controller ledger and starts only eligible undispatched work; it never resumes a model conversation.

The consumer reads `poc-exports/cap8-serial-public-toy-v2/latest.json`, resolves its relative snapshot paths under that directory, verifies each SHA-256, then reads summary and parallel reports. It must inspect evidence kind, collection status, stop reason, coverage and remaining budget. Schema rejects unexpected fields and unsafe values. Exports and campaign metadata are ignored by Git; producing an export does not publish it. Immutable snapshots plus the pointer permit safe repeated export after partial outcomes.

## 6. Remaining blockers and next step

Code and offline verification are complete; **functional live automation remains unverified**. CodexSandboxOffline does not inherit the ordinary Windows user's CLI authorization. This controller supplies no credential transfer, login, daemon, listener, queue, persistent scheduler or remote-initiation bridge. An authenticated ordinary-user start is still required for any later approved live test; a dot can read the safe export through its existing project access.

The installed compatible Code Mode host and effective model-selected tool mode have not been demonstrated under the retained isolated argv. `--ignore-user-config` is deliberately retained to exclude arbitrary user MCP/hooks/instructions. If host availability depends on configuration excluded by that flag, resolve the supported isolated-runtime prerequisite before dispatch; do not drop the restriction or install/change security implicitly. Unknown startup JSON/stderr diagnostics, missing accounting and unresolved reservations stop further launches while preserving observed cost. No installation, auth or security changes were made.

Stock read-only access is not a hidden-grader read jail; strict secrecy, backend confirmation, per-network-request receipts and subscription savings are not claimed. The [pinned tool selector](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/core/src/tools/mod.rs#L82) explains why false feature toggles do not override a model-selected mode; the [pinned event contract](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/exec/src/exec_events.rs#L1) defines stage usage. [Official configuration guidance](https://learn.chatgpt.com/docs/config-file/config-reference) supplies current context, not version attestation.

Next: review these verified code/export artifacts, retain the same private data-dir, and separately authorize the fixed small live test only after ordinary-user runtime prerequisites are verified without inference. Its first authorized P01 W attempt is the compatibility observation and consumes a budget slot; there is no free smoke test. This implementation/verification task authorizes no new model launches.
