# Измеренная готовность host и оставшийся авторизованный прогон

Версия: 2026-10-02. Код и offline-проверки продолжают сохранённую паузу. Новых модельных запусков: **0**. Реальный бюджет: **израсходовано 2/8, осталось максимум 6**. Две исторические ошибки старта остаются ошибками; их token receipts остаются учтёнными.

## Реализовано и наблюдалось

Установленный соседний `codex-code-mode-host.exe` завершил ограниченный stdio-handshake с protocol V1 и обеими capability, запрашиваемыми закреплённым клиентом: `session-cell-execution-resource-limits` и `yield-observation`. Собственный subprocess завершился успешно с пустым stderr после закрытия stdin. Проверка не использовала socket, service, JavaScript session, запрос модели, установку или изменение авторизации. Это подтверждает готовность протокола компонента, но не успешный модельный прогон или проверенную sandbox isolation.

Новый `runtime_host.py` закрепляет hashes обоих binaries до spawn, следует проверенному разрешению соседнего файла в bundle, отклоняет альтернативные resource layouts, отправляет framed hello клиента, проверяет единственный ответ и завершает только собственный child при timeout. CLI SHA-256: `34549ded6e2aee87c911c62d025e52e26c488683d0f489cd68f756baef1a6df6`; host SHA-256: `850eca242991c4271d1b0fd42e096423efac0046e984f9d2124319dae181a945`. У host нет поддерживаемого version switch, поэтому отдельная версия сборки host не заявляется.

Preflight контроллера теперь требует измеренный handshake до резервирования stage. `RuntimeReviewed` — устаревшая опция совместимости; она больше не предоставляет допуск готовности. Ошибка host даёт `host_readiness_failed` и не расходует новый stage. PowerShell wrapper находит существующий проверенный bundle, если native CLI отсутствует в PATH; Python по-прежнему проверяет его hash. Overrides selectors host/tool-mode не добавлены, существующие ограничения capabilities сохранены. Hash исходника helper входит в устойчивый provenance manifest; ранее привязанный к другим исходникам ledger останавливается, а не сбрасывается и не возвращает бюджет.

Источники: [bundle resolution](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/install-context/src/lib.rs), [client handshake](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/code-mode/src/remote_session/connection.rs), [framing](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/code-mode-protocol/src/host/codec.rs), [model-derived tool mode](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/core/src/tools/code_mode/mod.rs).

## Проверки и доказательства

Offline suite теперь содержит **44 tests**: прежние 41 плюс совместимость/обрыв host frame, pinning binary до spawn и stdio/timeout cleanup собственного child. Synthetic preflight test также доказывает отклонение неуспешного handshake; synthetic run/resume test проходит без прежнего attestation switch. Обычный и оптимизированный Python проходят с нулём failures, errors и skips; PowerShell parser, AST, strict JSON и diff checks проходят. Доказательства: `offline-validation-2026-10-02.json`, `offline-validation-optimized-2026-10-02.json` в каталоге эксперимента. Synthetic receipts и exports помечены `SYNTHETIC_FIXTURES`; они не доказывают успешный модельный прогон.

Synthetic export проекта пересоздан, hashes snapshots проверены. Consumers читают `poc-exports/cap8-serial-public-toy-v2/latest.json`, затем проверяют hashes указанных snapshots. Реальный ledger этим диагностическим действием не инициализирован и не продвинут. Существующие незакоммиченные отчёты, task bytes и посторонние материалы сохранены; приватные runtime streams исключены из публикации.

## Оставшийся блокер и следующий шаг

Executor `CodexSandboxOffline` не наследует ChatGPT-авторизацию обычного пользователя Windows. Поэтому авторизованный inference требует терминала обычного пользователя. Копирование credentials, вход в аккаунты, GUI bridge и постоянный listener не предпринимались. Измеренный sibling-handshake и defaults закреплённых исходников не доказывают effective startup configuration native exec или model-derived tool mode живого turn. Actual model и sandbox isolation остаются непроверенными; runtime diagnostics продолжают останавливать прогон, а не приниматься за успешные ответы.

Из корня проекта одна пользовательская команда выполняет неизменный зафиксированный план и автоматически записывает export:

```powershell
& '.\docs\experiments\toy-poc-v1\run-poc.ps1' -DataDir (Join-Path (Split-Path (Get-Location).Path -Parent) 'LLM-PoC-cap8') -Run -AcceptUnverifiedModelAndIsolation
```

При каждом restart повторно используйте тот же приватный data directory. Команда проверяет subscription/authentication и host до inference; она может выполнить максимум 6 оставшихся calls в фиксированном порядке задач, с bounded takeover при наблюдаемой ошибке. Не запускайте её из executor. В этой работе команда не выполнялась. Её последующие runtime errors и receipts нужно проверить через безопасный export без retries или выхода за ledger cap.
