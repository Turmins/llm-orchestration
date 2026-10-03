# Measured host readiness and remaining authenticated run

Version: 2026-10-02. Code and offline verification follow the saved pause. New model launches: **0**. Real budget: **2/8 consumed, at most 6 remaining**. The two historical startup failures remain failures; their token receipts remain charged.

## Implemented and observed

The installed sibling `codex-code-mode-host.exe` completed a bounded stdio handshake with protocol V1 and both capabilities requested by the pinned client: `session-cell-execution-resource-limits` and `yield-observation`. The owned subprocess exited successfully with empty stderr after stdin closed. No socket, service, JavaScript session, model request, installation or authentication change was involved. This establishes protocol readiness of that component, not successful model execution or verified sandbox isolation.

The new `runtime_host.py` pins both binary hashes before spawn, follows the inspected bundle's sibling resolution, refuses alternate resource layouts, sends the client's framed hello, validates a single response and reaps only its own child on timeout. CLI SHA-256: `34549ded6e2aee87c911c62d025e52e26c488683d0f489cd68f756baef1a6df6`; host SHA-256: `850eca242991c4271d1b0fd42e096423efac0046e984f9d2124319dae181a945`. The host has no supported version switch, so no independent host build version is asserted.

The controller's preflight now requires the measured handshake before stage reservation. `RuntimeReviewed` is a deprecated compatibility option; it no longer grants readiness. Host failure produces `host_readiness_failed` and consumes no new stage. The PowerShell wrapper resolves the existing inspected bundle when the native CLI is absent from PATH; Python still verifies its hash. No host/tool-mode selector overrides were added, and existing capability restrictions remain. The helper's source hash is part of the durable provenance manifest; an existing differently bound ledger fails closed rather than being reset or refunded.

Sources: [bundle resolution](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/install-context/src/lib.rs), [client handshake](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/code-mode/src/remote_session/connection.rs), [framing](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/code-mode-protocol/src/host/codec.rs), [model-derived tool mode](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/core/src/tools/code_mode/mod.rs).

## Verification and evidence

The offline suite now contains **44 tests**: the prior 41 plus host frame compatibility/truncation, binary pinning before spawn, and stdio/timeout child cleanup. The synthetic preflight test also proves failed handshake rejection; the synthetic run/resume test proceeds without the old attestation switch. Normal and optimized Python pass with zero failures, errors or skips; PowerShell parser, AST, strict JSON and diff checks pass. Evidence: `offline-validation-2026-10-02.json`, `offline-validation-optimized-2026-10-02.json` in the experiment directory. Synthetic receipts and exports are labelled `SYNTHETIC_FIXTURES`; they are not evidence of a successful model run.

The synthetic project export was regenerated and its snapshot hashes verified. Consumers read `poc-exports/cap8-serial-public-toy-v2/latest.json`, then verify referenced snapshot hashes. The real ledger has not been initialized or advanced by this diagnostic. Existing uncommitted reports, task bytes and unrelated materials were preserved; private runtime streams were excluded from publication.

## Remaining blocker and next step

The executor `CodexSandboxOffline` does not inherit the ordinary Windows user's ChatGPT authorization. Authenticated inference therefore requires the ordinary user's terminal. No credential copying, account login, GUI bridge or persistent listener was attempted. The measured sibling handshake and pinned source defaults do not prove native exec's effective startup configuration or model-derived tool mode for a live turn. Actual model and sandbox isolation remain unverified; runtime diagnostics continue to fail closed rather than being accepted as successful answers.

From the project root, one user-side command runs the unchanged frozen plan and writes the export automatically:

```powershell
& '.\docs\experiments\toy-poc-v1\run-poc.ps1' -DataDir (Join-Path (Split-Path (Get-Location).Path -Parent) 'LLM-PoC-cap8') -Run -AcceptUnverifiedModelAndIsolation
```

Reuse that same private data directory on every restart. The command performs subscription/authentication and host checks before inference; it can launch at most 6 remaining calls in the fixed task order, with bounded takeover on visible failure. Do not run it from the executor. This task did not run that command. Its eventual runtime errors and receipts must be inspected through the safe export without retrying or spending beyond the ledger cap.
