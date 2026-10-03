# Windows four-task CLI PoC

Historical instructions. The active serial controller, fixed small plan, required data directory and current blockers are described in [verified controller fixes](controller-audit-fixes-2026-10-01.md). Commands below retain the earlier interface and must not be used with the current wrapper.

Version: 2026-10-01. This is an executable, bounded diagnostic for the user's ordinary Windows terminal, using the existing four frozen original tasks. No models were run while preparing this runner. It does not revive the larger benchmark.

## Launch

From the repository root in Windows PowerShell 5.1 or PowerShell 7, with existing Python 3.9+ and the user's already authenticated CLI 0.159.2:

```powershell
& .\docs\experiments\toy-poc-v1\run-poc.ps1 -CodexExe (Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin\de8a38d2100ae498\codex.exe') -Run -AcceptUnverifiedModelAndIsolation
```

This uses the installation suffix supplied by the user without publishing their personal path. If the app updates the executable location/version, review the adapter rather than silently using another version. An existing Python executable can be supplied with `-PythonExe`; otherwise the wrapper uses `py.exe -3` or `python.exe`. Nothing is installed. Omitting `-Run` performs only preflight. ExecutionPolicy, credentials and persistent account/security settings are never changed. If local policy blocks the script, report that restriction; do not bypass it.

The [PowerShell entry point](../experiments/toy-poc-v1/run-poc.ps1) launches the [standard-library controller](../experiments/toy-poc-v1/cli_runner.py). The command's parameters and paths were statically checked; it was **not executed on Windows here**. No PowerShell parser is available in the cloud, so PowerShell syntax/runtime validation on Windows remains outstanding.

## Preflight and spending boundary

Before inference the controller checks the frozen task checksum, native executable, version, global/exec help, ChatGPT login and available feature toggles. It refuses an API-key/provider environment override without reading or printing secret values. Each inference requests the built-in OpenAI provider and `forced_login_method="chatgpt"`; there is no paid API fallback, login flow, installation or credit purchase.

The [official model catalog](https://learn.chatgpt.com/docs/models) lists `gpt-6-luna` and `gpt-6.1-sol`, subject to account/client availability. The reviewed CLI has no documented non-inference model-list subcommand. Account access to both models therefore remains unverified before their first task; unsupported model errors stop the series. No extra discovery model calls are made. Confirm included subscription capacity before launch: CLI login does not establish remaining allowance or exclude automatic use of existing extra credits. The controller cannot enforce an included-only quota boundary; do not launch if that boundary is uncertain. It does not change credit/account settings.

## Strategies, routing and limits

W requests `gpt-6-luna`, E requests `gpt-6.1-sol`; both request `medium` and `default` service tier. Actual model, effort and tier are unconfirmed. One fresh CLI invocation handles each task/stage, without resume/fork. Initial order alternates W/E and E/W by task. W-only freezes the single W answer. W→E reuses that same W artifact and adds one fresh E takeover only for a frozen visible-rule failure. E-only independently receives the original task. No repair loops or controller retries. Built-in provider retry settings cannot be overridden by a custom provider entry; internal transport retries are not claimed disabled. Reported stage totals are retained in full, and any incomplete/error receipt stops the series. Total comparative invocations: 8–12. Shared W counts once physically and once in each logical strategy; the policy estimates are dependent, not independent samples.

A malformed candidate is a visible failure. Missing usage, process failure, timeout, reroute, tool activity or unsupported events stop the series; they never trigger E. Handoff contains the original packet, untrusted candidate and visible evidence only. The existing independent algorithmic grader runs after candidates and their byte hashes are frozen; hidden acceptance never controls routing. No hidden tests/reference answers are placed in prompts or task workspaces.

A separate `-ForcedHandoffOnly` option, together with the launch switches, runs exactly one W and one E on P03 under a new run directory, excluding it from comparative totals. It is not enabled by default. All budget values are plans: at most 12 comparative stages, 180 seconds per client process, 16000 prompt UTF-8 bytes, post-receipt stopping thresholds of 32000 input and 4000 output tokens per stage and 384000 input / 48000 output overall. These replace the earlier hypothetical 4000-input limit for this adapter: the user-reported arithmetic smoke already used 15445 input tokens. The CLI has no verified hard output-token control here; post-receipt thresholds can be exceeded by the current stage and are not spending ceilings. Killing a client on timeout does not prove server cancellation. Stop and reconcile; never retry automatically.

## Receipts and actual-model limitation

Each unique private run directory is printed under the OS temporary directory; prior results are never overwritten. Every stage stores UTF-8 prompt bytes, untouched stdout JSONL and separate stderr, argv/exit/timestamps, candidate hash and a journal record. Python supplies binary stdin to CLI using the positional `-`, avoiding PowerShell native-pipeline encoding and quoting differences. Preserve the directory before temporary-file cleanup. Raw logs can contain private runtime information; do not publish them automatically.

The parser accepts a completed fresh thread with one turn and mandatory input/output counters. Turn usage is sufficient task/stage accounting; per-network-request telemetry is not required. Thread ID is retained; absent request/response/turn IDs, cache and reasoning fields remain `null`. Failures and partial receipts remain in the ledger; full totals become unavailable, while explicitly named known subtotals remain inspectable. CLI-reported zero cache is retained as reported, not promoted to a verified backend measurement.

`input_tokens + output_tokens` adds each reported total once. Cached input, cache writes and reasoning are separate reported components, never added again. Cache read/write disjointness and an uncached tariff bucket are not inferred. No dollar, allowance or savings conversion is produced. The new stage parser deliberately does not use the older strict single-network-call validator.

The [JSONL documentation](https://learn.chatgpt.com/docs/non-interactive-mode), [public event schema](https://github.com/openai/codex/blob/main/codex-rs/exec/src/exec_events.rs) and [event processor](https://github.com/openai/codex/blob/main/codex-rs/exec/src/event_processor_with_jsonl_output.rs) were inspected. Current public source copies thread-total usage into the completion event, can default absent usage to zero, discards model-verification notifications and emits reroutes as an error item. The adapter uses fresh threads, rejects zero-input receipts for nonempty prompts and stops on error items. These public sources are not attestation of the installed Windows binary. No documented confirmed-model field is available in this adapter: `actual_model=null`; absence of reroute is not confirmation. A run is explicitly marked `COMPLETED_UNVERIFIED_MODEL_AND_ISOLATION`, never a confirmed Luna-versus-Sol economic result. The launch acknowledgement accepts this diagnostic limitation, not spending beyond the subscription.

## Isolation and evidence limits

Each stage receives an empty temporary cwd outside the repository and logs. Document loading is suppressed; supported shell, execution, apps, plugins, browser, computer, delegation and memory features are disabled for that invocation. The controller uses ephemeral sessions, read-only sandbox and no approval escalation. User config is not loaded for inference; existing auth and managed policies remain, with no persistent changes. Relevant settings are documented in the [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

This is best-effort tool restriction, **not a verified filesystem read jail**. Managed/global extensions may remain, and JSONL is not proof that every hidden runtime action is exposed. Observed tool events invalidate the run, but post-run detection cannot undo access. Consequently the grader's algorithm is independent while its secrecy on this ordinary host is unverified. A confirmed hidden-acceptance experiment needs a separately validated read-isolated runtime; the acknowledgement does not waive that scientific limitation.

## Validation

[Tests](../experiments/toy-poc-v1/test_cli_runner.py): 16 synthetic checks passed, including a synthetic local subprocess for byte I/O, missing/invalid counters, failed processes, replay/conflicts, reroutes/tools, shared-work accounting, visible-only escalation and frozen-answer grading. The existing synthetic harness also passed. The supplied Windows counters were wrapped in explicitly synthetic events for parser arithmetic: 15445 input, 12032 cached, 0 cache writes, 5 output, 0 reasoning yield 15450 reported input-plus-output, not a new measurement. The user's arithmetic answer 42 and successful Windows CLI execution are user-reported evidence; the original Windows JSONL was not accessed here. No real comparative calls, Windows execution, PowerShell parser test, account model discovery or validated sandbox-isolation test was performed in this preparation.
