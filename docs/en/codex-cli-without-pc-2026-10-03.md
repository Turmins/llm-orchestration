# Codex orchestration without the user PC

Date: 2026-10-03  
Status: documentation and public-source research; cloud execution is not verified

## Conclusion

For this public repository, the least-complex supported starting point is a normal Codex Cloud task using ChatGPT sign-in. Codex Cloud can work while the user PC sleeps. Running this project's own nested CLI orchestrator inside that task remains a separate, unverified compatibility question. [Codex Cloud](https://learn.chatgpt.com/docs/cloud), [authentication](https://learn.chatgpt.com/docs/auth)

A continuously available user-hosted runner is a different architecture. Headless ChatGPT login is documented, but the advanced account-auth CI guide explicitly excludes public/open-source repository workflows. A private VM or a manually selected checkout does not establish an exception to that restriction. [Headless login](https://learn.chatgpt.com/docs/auth#login-on-headless-devices), [advanced CI authentication](https://learn.chatgpt.com/docs/auth/ci-cd-auth)

## Evidence and scope

This review reads official documentation and the public OpenAI Codex source. It does not run repository code, start inference, provision services, access the user PC, or transfer credentials.

The supplied project checkpoint for October 3 reports:

- The task safely ended its own command sessions; system-wide process absence was not established
- The project launch budget remains 3 consumed out of a cap of 8, with at most 5 remaining
- No new inference was launched and no tests were run
- The six-event ledger and its hash remained unchanged
- An uncommitted partial policy change in cli_runner.py remains untested and must be preserved

These are supplied checkpoint observations, not findings independently reproduced by this documentation review. Current cloud runtime validation was unavailable. The latest safe diagnostic export established adjacent_intervals_overlap as the P01 visible failure; five earlier boundary checks validated the checker. The earlier report's unresolved-failure statement is superseded by that evidence. The local partial policy change is not part of the verified remote code.

The installed local CLI was reported as 0.159.2; the historical managed-cloud attempt used 0.159.0-alpha.3. The corresponding public release commits are ff6aec96948b70d94983af2641a6b67c94faeff5 and 3b01b36fa5eb96ba82a776bd3c2fc57f8969181f. Current main source was separately inspected at [b741e480e203f037ca726bc2a76d99a8e8668e66](https://github.com/openai/codex/commit/b741e480e203f037ca726bc2a76d99a8e8668e66). Source behavior is not proof that an installed binary or managed host behaves identically. [0.159.2 release](https://github.com/openai/codex/releases/tag/rust-v0.159.2), [alpha.3 release](https://github.com/openai/codex/releases/tag/rust-v0.159.0-alpha.3)

## Available architectures

### Managed Codex Cloud

A published environment supplies the prepared filesystem; each new task receives an isolated workspace. Reopening the same task preserves its saved files, including uncommitted edits and installed tools. Default saved VM state is recoverable for up to seven days after the last turn or resume. This is task persistence, not a documented always-on service guarantee. Save important results in source control. [Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments)

The older cloud-environment guide now describes the legacy experience. Its twelve-hour container-cache figure should not be substituted for the current task-state retention rule. [Legacy cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environment)

### User-hosted remote CLI

A remote/headless host can use codex login --device-auth after device-code login is enabled for the account or workspace. User browser approval is still required. Saved authentication is reused by codex exec. Authentication establishes account identity, not entitlement to every model or indefinite unattended operation. [Authentication](https://learn.chatgpt.com/docs/auth), [non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)

For trusted private automation, the account-auth CI guide requires preserving refreshed auth state and using one machine or serialized job stream per auth.json copy. It recommends API keys for ordinary CI and prohibits this workflow for public/open-source repositories. Do not deploy that pattern in this repository's public CI. [Advanced CI authentication](https://learn.chatgpt.com/docs/auth/ci-cd-auth)

The runner's availability, storage, process supervision and operating costs would require a separately chosen hosting setup. No such setup was provisioned or verified here.

### Separate subscription-backed integration options

Official Sign in with ChatGPT documentation describes plan-usage OAuth for open-source/locally hosted apps and a self-hosted VM procedure. This is a separate client-registration and consent architecture, not a workaround using copied CLI credentials. Paid or remotely hosted app offerings follow a separate interest process. [Plan-usage overview](https://developers.openai.com/siwc/token-sharing-open-source), [self-hosted VMs](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms)

Its Codex App Server integration requires the application to manage token renewal. Preview requests require streaming and store:false; some Responses fields and hosted tools are unsupported. Local thread history and resume remain available. Compatibility with this project and account is untested. [App Server integration](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server), [preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)

Codex access tokens are documented for Business and Enterprise workspaces. Workload identity federation for Codex is a workspace-enabled beta. Neither should be assumed available under an unspecified personal subscription. [Access tokens](https://learn.chatgpt.com/docs/enterprise/access-tokens), [workload identity federation](https://developers.openai.com/api/docs/guides/workload-identity-federation)

The Agents API self-hosted executor uses application and environment API keys. It does not document a way to convert a normal ChatGPT CLI login into subscription-funded Agents API access. [Self-hosted API sandboxes](https://developers.openai.com/api/docs/guides/agents-api/environments/self-hosted)

## Writable runtime state and the historical failure

The historical alpha.3 attempt reported ChatGPT login but failed during internal App Server startup on a read-only filesystem. That establishes a startup blocker, not successful inference or a proven root cause for every state path.

Codex documents CODEX_HOME for config, auth, logs and sessions, and CODEX_SQLITE_HOME for SQLite state; an explicit sqlite_home setting takes precedence. A specified CODEX_HOME must already exist. [Environment variables](https://learn.chatgpt.com/docs/config-file/environment-variables), [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)

Both release sources resolve SQLite storage as sqlite_home, then CODEX_SQLITE_HOME, then CODEX_HOME. The runtime creates its directory, opens and migrates several databases; writable SQLite connections use WAL. Directory and sidecar-file writes therefore matter. [0.159.2 path resolution](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/config/mod.rs#L4059-L4076), [alpha.3 path resolution](https://github.com/openai/codex/blob/3b01b36fa5eb96ba82a776bd3c2fc57f8969181f/codex-rs/core/src/config/mod.rs#L4058-L4075), [runtime initialization](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/state/src/runtime.rs#L103-L196), [writable SQLite connection](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/state/src/sqlite.rs#L296-L311)

Candidate: place the child CLI's runtime state in explicitly allowed writable directories, separate from the checkout and from the managed parent's state. This is a configuration hypothesis. It has not repaired the historical failure in a test. Redirecting storage does not override enforced permissions, and a new CODEX_HOME must not be assumed to inherit authentication.

## Persistence and security boundaries

codex exec supports saved-session resume; --ephemeral suppresses session rollout persistence. Persistent history requires durable state storage independently of the repository checkout. [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)

Do not treat read-only agent commands as a promise that the CLI itself performs no runtime-state writes. Keep credentials out of the public repository, artifacts and logs. File-based auth is a password-equivalent access-token cache. [Advanced configuration](https://learn.chatgpt.com/docs/config-file/config-advanced#config-and-state-locations), [credential storage](https://learn.chatgpt.com/docs/auth#credential-storage)

For a later custom integration, prefer local stdio transport. Current App Server documentation labels WebSocket transport experimental/unsupported and warns that non-loopback listeners can accept unauthenticated connections by default unless explicit transport authentication is configured. Do not expose a runner control port as a shortcut. [App Server transport](https://learn.chatgpt.com/docs/app-server#protocol)

Sandbox restrictions and approval policies are separate controls; disabling approvals does not create missing filesystem permission. A future test should use the least necessary permissions, without broad full-access escalation. [Agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security)

## JSONL usage and model identity

1. codex exec --json emits JSONL events. The successful terminal event contains usage. Capture the complete private stream and stderr, then produce a sanitized summary. [Non-interactive output](https://learn.chatgpt.com/docs/non-interactive-mode#make-output-machine-readable)
2. Both investigated release schemas contain input_tokens, cached_input_tokens, cache_write_input_tokens, output_tokens and reasoning_output_tokens. Parsers should retain available fields and distinguish absent values from zero. [0.159.2 schema](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/exec/src/exec_events.rs#L59-L73), [alpha.3 schema](https://github.com/openai/codex/blob/3b01b36fa5eb96ba82a776bd3c2fc57f8969181f/codex-rs/exec/src/exec_events.rs#L59-L73)
3. The processor copies cumulative thread tokenUsage.total into turn.completed.usage. Fresh one-turn threads have no earlier-turn baseline, which matches this project's reported fresh-thread-per-stage design. No current ledger double-counting is established. Resumed threads need a validated cumulative baseline/delta; do not blindly sum their terminal totals. [0.159.2 processor](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L118-L128), [alpha.3 processor](https://github.com/openai/codex/blob/3b01b36fa5eb96ba82a776bd3c2fc57f8969181f/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L509-L565)
4. Failed/interrupted runs may lack terminal usage; absent updates can yield default zeros. Missing/zero telemetry is not proof of no consumption. Mark accounting incomplete and keep budget reservation conservative. [Terminal-event handling](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L509-L565)
5. Record requested model, provider, reasoning effort, speed mode, binary version, result status and observed reroutes separately. Normal exec thread.started identifies the thread, without proving the served model. Reroutes are rendered as error-type item text. [Exec model events](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L494-L535)
6. Cached input is a subset of input; reasoning output is a subset of output. Do not add those detail counters a second time. Retain cache-write separately when present; do not infer a subscription charge from it. [Upstream usage mapping](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/codex-api/src/sse/responses.rs#L117-L155), [token-category explanation](https://developers.openai.com/api/docs/guides/agents-api/observability#understand-token-usage)
7. App Server exposes structured usage with thread and turn identifiers, cumulative total and last counters; last is the latest model response, not the entire multi-response turn. A resumable integration should baseline cumulative totals after resume and compute turn deltas. Its structured reroute fields improve attribution without proving an exact backend model snapshot. [Usage protocol](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/app-server-protocol/src/protocol/v2/thread.rs#L1875-L1965), [counter accumulation](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/protocol/src/protocol.rs#L2275-L2314), [reroute protocol](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/app-server-protocol/src/protocol/v2/model.rs#L185-L194)
8. Server-reported model headers are handled internally. The inspected mismatch helper assigns a fixed reroute-reason value, so that reason alone cannot establish the actual policy cause. A model catalog is not an entitlement test. [Model-header handling](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/codex-api/src/sse/responses.rs#L49-L76), [mismatch handling](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/session/mod.rs#L4028-L4065), [catalog caveat](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server)

Token telemetry, project launch counts and remaining subscription allowance are different measurements. Local/cloud work shares plan allowance; model, context, tools, reasoning and caching affect consumption. Consult the usage dashboard for actual limits and reset times. No API-price conversion or fixed token-to-subscription-quota formula is established here. [Pricing and limits](https://learn.chatgpt.com/docs/pricing)

## Recommendation and minimum future test

Recommendation: restore access to the saved managed Codex Cloud environment first. Use ordinary cloud tasks for the public repository. Only then test whether this project's own CLI orchestration can run inside its allowed runtime boundary. Do not build an always-on daemon or introduce a new OAuth architecture before this basic compatibility result is known.

Proposed next verification, not executed in this documentation study. New hosting, credential grants or security changes require the relevant approval:

1. Preserve the uncommitted partial change before any implementation. Start from a clean, approved cloud checkout and record the exact CLI and child App Server versions
2. Perform a zero-inference preflight: inspect effective configuration, verify permitted runtime directories and initialize an isolated stdio App Server without starting a model turn. Success means initialization and clean shutdown complete without state-write errors
3. If preflight succeeds and account authentication is available through a supported user-approved flow, first verify access to the authoritative campaign ledger without resetting or duplicating it, then reserve at most one additional project launch and run one small read-only fresh-thread prompt
4. Require exit status, terminal success, valid JSONL, explicit usage completeness and requested-versus-observed model evidence. Record any routing uncertainty. Check the project ledger and usage dashboard separately
5. Stop after that one launch or the first blocker. Do not automatically retry inference, widen permissions, copy managed credentials or overwrite the preserved local partial change

This plan is a bounded validation proposal, not a claim that the cloud runner now works. Failure before inference leaves compatibility unresolved; a successful single turn still does not prove token refresh, resume, concurrent execution or always-on reliability.

