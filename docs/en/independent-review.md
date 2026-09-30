# Independent Architecture Reassessment

Verification date: 2026-09-30. `задача.md` (111 lines) and `hierarchical-llm-architecture-review.md` (986 lines) were read in full. The main document has been updated in full and published in Russian and English; the independent conclusion and reasons for the changes follow below.

The original is substantially stronger than the list of requested revisions might suggest. It already contains the right objective, two configurable roles, independent acceptance, protected checks, bounded retries, experiments from saved checkpoints, and audits of accepted results. There is no basis for rebuilding this core. The economic advantage of cheap-first remains unproven.

The model bindings and implementation plan need to change first. I propose testing Codex CLI/App Server as the existing execution environment, leaving policy, state, protected acceptance, and measurement to a custom layer. The initial candidates are GPT-6 Luna and GPT-6.1 Sol; Sol is compared as the sole expert and as a direct executor. Astra remains a separate candidate rather than the mandatory end of a ladder. Names and rates are confirmed by the current [model cards](https://developers.openai.com/api/docs/models); suitability for particular tasks requires an experiment.

Official documentation confirms explicitly requested delegation without Ultra. Ultra is associated with proactive delegation in the applicable product; Ultrafast is a separate speed setting with its own usage conditions. [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [speed](https://learn.chatgpt.com/docs/agent-configuration/speed). The presence of subagents does not prove isolation, correct integration, or independent verification.

A material version discrepancy: the online [App Server](https://learn.chatgpt.com/docs/app-server) documentation describes detached review as a fork, while the schema of the installed `codex-cli 0.159.0-alpha.3` already marks that option deprecated and recommends a new session with inline review. Independent verification should therefore use fresh context with controlled inputs and separate file state. Neither a new ID nor a different model guarantees independent errors.

## Change table

Priority P0 means before the corresponding experiment; P1 means a refinement of measurement and subsequent decisions; P2 means only after an observed need. “Proposal” denotes an architectural conclusion rather than a vendor-declared capability.

| Section | Change | Rationale | Source / required experiment | Priority |
|---|---|---|---|---|
| 1, 1.1 | Inherited provisions, facts, proposals, and hypotheses are separated | Avoid crediting the revision with ideas that already existed | Complete original; user request | P0 |
| 1.1, 8, 9, 11 | Model names in policy are replaced with W/E roles; candidate registry updated | The expert need not be Astra; Sol need not be an intermediate tier | [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra); access check and E3 | P0 |
| 2.1–2.6 | K, total cost, conditional transitions, VOI, reliability, and limits retained | The mathematical core matches the objective; there is no reason to remove it | Algebra checked; original constraints preserved | P0 |
| 2.7, 10 | API costs, actual payments/credits, and subscription quota separated | API-equivalent cost does not measure included-quota savings | [Codex pricing](https://learn.chatgpt.com/docs/pricing); observation of selected usage windows | P0 |
| 2.7 | Cache-write bucket and dated rates added; history separated from cache | A new W result cannot automatically count as E's cached input | [API pricing](https://developers.openai.com/api/docs/pricing), [prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching); usage verification | P0 |
| 3, 11.4 | W-only, E-only, and W→E are simple comparable alternatives | Comparing only with the most expensive executor exaggerates the benefit | Proposal; whole-task E1, identical acceptance and full cost | P0 |
| 4.1 | Codex is the runtime candidate; custom layer limited to actual gaps | No need to rebuild the agent environment before checking what already exists | Installed CLI help/schema; [App Server](https://learn.chatgpt.com/docs/app-server) | P0 |
| 4.1 | Desktop, CLI, App Server, and API distinguished; Ultra and Ultrafast distinguished | A capability of one product does not automatically transfer to another | [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Speed](https://learn.chatgpt.com/docs/agent-configuration/speed), per-account discovery | P0 |
| 4.2, 15 | Technical and economic stages receive distinct inputs and exit conditions | A protocol schema does not prove actual control/isolation | Technical probes without implementing an orchestrator; then E1/E2 | P0 |
| 6.2 | Existing independence clarified: fresh history and separate file permissions | Resume/fork/detached do not equal clean context | Documentation and observed schema discrepancy; input-provenance test | P0 |
| 7, 9.8 | Checkpoint includes history, files, environment, tools, and limits | Conversation history and file state are distinct parts of state | Proposal; frozen-checkpoint reproduction | P0 |
| 8, 9.9, 11.4 | Retry, consultation/application, and takeover are alternatives; consultation has explicit stop limits | The original linear chain could impose unnecessary expense | Proposal; matched E2, one optional branch before takeover | P0 |
| 8, 9.8 | Counterexample/test/invariant and reviewer-only distinguished; not all included initially | Their usefulness and authority differ | Oracle/requirement-mapping check; E6 when needed | P1 |
| 10, 11 | Independent labels, accepted-result audits, propensity, and statistical limits retained | Studying only known failures introduces bias | Original; E1/E2, independent audit and project/time holdout | P0 |
| 12 | R01–R24 retained; risks of false runtime guarantees and incorrect billing/cache added | New dependencies require explicit risk accounting | Technical probes, usage reconciliation, R25/R26 | P1 |
| 13–15 | Losing conditions retained; unresolved questions split into critical and deferred | A valid outcome is simple Codex/direct-model use without a custom runtime | Proposal; stage-specific gates and lifecycle economics check | P0 |

## What is established and what is not

Current official pages, the limits on transferring findings from the cited studies, and the local schema were checked. The original qualifications are retained: FrugalGPT/RouteLLM do not prove the economics of long-running agentic work; correlated-error literature does not provide probabilities for the selected pair; a small pilot cannot certify rare-error rates.

Actual account-level model availability, execution of start/resume/fork, process cancellation, isolation, real cache hits, quota precision, and savings were not tested. They are listed as technical/economic experiments, not guarantees. No model runs, orchestrator implementation, or settings changes were performed during the research.

## Critical unresolved questions only

1. Which exact client/build and authentication mode should be used, which W/E configurations are actually available, and what finite spend/quota/time limit applies to the authorized fixture?
2. Which safe fixture and protected requirements/checks should be used, and where are the permitted file and tool boundaries?
3. Which usage/quota/billing data are available, and is their precision adequate for the claimed comparison?
4. Before the economic stage: which single real task family and independent oracle/audit represent the intended work?
5. What budget, quality/coverage/time constraints, minimum useful savings, and stopping rules should be set before drawing an economic conclusion? Work volume and maintenance cost are additionally required before deciding on a custom production controller.

Optimal decomposition depth, a third model tier, shadow review, and a trained router do not block the first technical experiment.

## Artifacts and integrity checks

- `hierarchical-llm-architecture-review-updated.md` — the complete, consistent edition in the language of the current directory, including a short appendix for standalone reading.
- `first-experiment.md` — a compact appendix for practical discussion of execution.
- This file — the independent conclusion, change table, and critical questions.

The documents are published in parallel `docs/en` and `docs/ru` directories with a shared index. Substantive conclusions, formulas, constraints, and external sources are preserved. Internal identifiers and file-transfer details are excluded from the public edition.
