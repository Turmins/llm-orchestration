# Исправления controller по независимому архитектурному аудиту

Версия: 2026-10-01. Объём: код проекта и offline-проверки. Новых inference-запусков: **0**. Реальный бюджет PoC остаётся **2/8 израсходовано, максимум 6 осталось**. Этот отчёт заменяет исторические инструкции запуска cap8 и продолжения; сами документы и свидетельства сохранены.

## 1. Результат и уровень доказательств

Активный controller на стандартной библиотеке теперь реализует последовательность W → публичные проверки → при необходимости один E takeover. Устойчивый учёт, восстановление и автоматический экспорт в проект реализованы и проверены синтетическими fixtures. Это независимая детерминированная проверка публичных toy-задач. Она не доказывает успешный модельный прогон, секретность невиданных задач, подтверждённую backend-модель, измеренную квоту подписки или экономию.

Фактический исходный checkout находился на HEAD `94b50f9b06aca06bcdfdb12a631923f5d79eef14`, с существующими правками runner/ledger и незакоммиченными отчётами. Reset, clean, stash и pull не применялись. Перед изменениями проверена копия редактируемого кода и индекса. Существующие аудит, runtime-свидетельства и исторические отчёты сохранены. Временное отключение executor прервало первую попытку; после переподключения команды заработали, а отсутствие предложенного плана/копии было подтверждено до их создания.

Реализация следует `docs/ru/architecture-audit-2026-10-01.md` и `docs/en/architecture-audit-2026-10-01.md`. В локальном checkout применимых AGENTS-файлов и каталога локальных skills не было. Двуязычное соглашение об отчётности соблюдено. OpenAI Docs применён для официальных сведений о конфигурации; поведение CLI отнесено к закреплённым исходникам, а не подвижной ветке.

## 2. Реальные изменения и причины

| Пункт | Реализованное поведение | Причина и ограничение |
|---|---|---|
| A4, A6 | Lock кампании и привязка каталога в проекте вместе с приватным OS lock защищают один ledger с цепочкой хешей. Prompt bytes и устойчивый reservation записываются до spawn. Обновления используют flush, fsync и атомарную замену в том же каталоге. | Конкурирующие controller, другой data-dir и исчезнувший привязанный ledger не могут незаметно получить новый cap8-бюджет. Это локальный файловый controller без службы или очереди. |
| A4, A6 | Исторические W/E-свидетельства импортируются один раз. Reservations остаются списанными до записанного наблюдения; неизвестные попытки нельзя перезапускать. Resume проверяет manifest, исходники и хеши артефактов. | Сбой после reservation консервативно учитывается. Доступные stdout и process metadata позволяют восстановить потерянную terminal-запись; неизвестный exit остаётся блокером. Повреждённый ledger никогда не сбрасывается. |
| A5, A8 | JSONL разбирается построчно с byte offsets, хешами строки/источника/receipt и сохранением usage observations. Одинаковые receipts учитываются один раз; конфликты сохраняют наблюдения и минимальную известную нижнюю границу. | Повреждённый хвост, неверный UTF-8, частичные receipts и error events больше не стирают ранее доступный числовой usage. Конфликтующее или неполное покрытие блокирует продолжение. |
| A1, A5 | Runtime, safety, покрытие usage, видимое решение и независимая correctness представлены отдельными полями. Неизвестные JSON diagnostics и непустой stderr блокируют продолжение. | Startup capability warning при exit zero может сохранить полный числовой receipt и правильный candidate, оставаясь непригодной попыткой. Исторические failures не превращаются в clean successes. |
| A2, A9 | Один W на плановую задачу, затем один E только при ошибке публичных JSON/schema/invariant-проверок и пригодных runtime/usage. Нет baseline, repair, forced handoff или автоматического retry. | Финальный grader вызывается только после остановки сбора; hidden-only ошибка не направляет следующую попытку. Ранее frozen-результаты сохраняются при позднем сбое. |
| A1, A7 | Конфликтующие Code Mode selector/host overrides удалены. Сохранены read-only sandbox, запрет escalation, ограничения инструментов, отключённый web и изоляция от произвольной пользовательской конфигурации. | Сохранён штатный выбор tool mode. Доступность host и effective mode не подтверждены; сохранение поддерживаемого host не оправдывает расширение permissions. |
| A3, A9 | Неизменяемые allowlisted JSON/RU/EN snapshots автоматически записываются в проект с атомарным финальным указателем и хешами. | Из экспорта исключены candidate content, raw logs, reasoning, диагностические сообщения, credentials, identities, environment/config dumps и абсолютные приватные пути. Dot читает файлы через доступ к проекту. |
| A10 | Явно заданы UTF-8 byte transport, native argv arrays и LF-политика исходников. Хеши working tree, LF и исторических Git blobs названы раздельно. | Оригинальные receipts не нормализуются перед хешированием; восстановленные исторические candidate hashes не выдаются за хеши оригинальных приватных свидетельств. |

Журнал представляет собой атомарно заменяемый JSON snapshot неизменяемой цепочки событий. Такая небольшая cap8-реализация исключает частичные хвосты журнала без базы данных и общего workflow framework. OS-crash tests покрывают окно reservation; устойчивость конкретного диска/файловой системы к потере питания не доказана.

Preflight требует CLI версии 0.159.2 и SHA-256 проверенного executable `34549ded6e2aee87c911c62d025e52e26c488683d0f489cd68f756baef1a6df6`. Несовпадение останавливает работу до выполнения бинарного файла; обновление требует отдельного пересмотра adapter.

## 3. Фиксированный малый тест и исторический учёт

Новый [зафиксированный план](../experiments/toy-poc-v1/small-test-plan.json) выбирает исходные задачи **P01–P03** именно в этом порядке до любого нового inference. P04 явно исключена из малого теста и присутствует в каждом отчёте. Замена задач по результатам запрещена. Максимальный будущий объём — **3 W + 3 E = 6 новых запусков** плюс два исторических, в пределах cap8. Если естественного takeover не будет, следует указать ноль; дополнительный вызов для его искусственного получения не нужен. Запрашиваемые модели остаются `gpt-6-luna` и `gpt-6.1-sol`, с medium effort и default speed. Actual model неизвестна.

| Историческое значение, предоставленное пользователем | W | E | Известная сумма |
|---|---|---|---|
| Input | 7629 | 8319 | 15948 |
| Cached input | 1792 | 0 | 1792 |
| Cache write | 0 | 0 | 0 |
| Output | 90 | 68 | 158 |
| Reasoning output | 66 | 44 | 110 |
| Process exit | unknown | 0 | — |
| Elapsed seconds | unknown | 7.1023351 | — |

Input plus output составляет **16106**. Cache/reasoning-компоненты повторно не прибавляются. Обе строки сохраняют startup capability failure Code Mode, user-supplied provenance и отсутствие оригинальных raw hashes. Отсутствующие optional counters остаются null; null не вызывает арифметических исключений. Исторический арифметический smoke находится вне этого бюджета и не импортируется.

## 4. Offline-проверки

Итоговый regression suite содержит **41 tests**. Обычный Python и режим оптимизации проходят с **0 failures, 0 errors, 0 skips**. PowerShell parser возвращает **0 errors**; проверки Python AST, strict JSON и git diff проходят. См. [обычное свидетельство](../experiments/toy-poc-v1/offline-validation-2026-10-01.json) и [свидетельство режима оптимизации](../experiments/toy-poc-v1/offline-validation-optimized-2026-10-01.json), содержащие хеши представлений исходников и число tests. Verifier блокирует неожиданные subprocess executables до spawn.

Покрыты corrupted JSONL после valid usage; completed receipts с runtime errors; partial/missing/zero/invalid counters; duplicate/conflicting receipts; failure записи reservation; process crash после reservation; recovery после failure terminal append; duplicate invocation; resume accounting; два реальных локальных Python-процесса, конкурирующих за OS lock; смена data-dir и исчезнувший/повреждённый ledger; provenance и reconstructed evidence; отсутствие hidden routing; bounded takeover и финальная ошибка E; poisoned candidate data; изменение candidate/receipt; export allowlists, counters, failure атомарного указателя, traversal и запрет Windows junction; native Windows argv; UTF-8/BOM/CRLF; JSON и паритет двуязычных отчётов.

Run/export проверены через synthetic captures. Необязательный демонстрационный экспорт в проект явно помечен `SYNTHETIC_FIXTURES`; вымышленные launches/counters не меняют реальный бюджет 2/8 и не доказывают успешную работу модели. При проверках inference executable Codex не запускался.

## 5. Точка входа, resume и контракт экспорта

Используйте один постоянный приватный каталог вне checkout и автоматически очищаемого временного хранения. Сохраняйте его для каждого restart; не выбирайте другой каталог для обхода бюджета. В игнорируемых metadata кампании проект хранит только хеш каталога. Raw prompts/stdout/stderr/process receipts и authoritative ledger остаются приватными, отдельно от stage workspaces. Каждый stage workspace содержит только публичный packet. Хеш каталога и разделение prompts не являются границами read secrecy.

Для offline-проверки из каталога controller:

```powershell
python -B -X utf8 verify_offline.py --out offline-validation-2026-10-01.json --demo-export
python -B -O -X utf8 verify_offline.py --out offline-validation-optimized-2026-10-01.json
```

После выбора `$PrivateData` следующая команда только восстанавливает/экспортирует учёт, не обращаясь к runtime:

```powershell
& .\docs\experiments\toy-poc-v1\run-poc.ps1 -DataDir $PrivateData -ExportOnly
```

Если не заданы ни Run, ни ExportOnly, выполняется только preflight версии/help/метода login/имён features, без inference. Будущий явно разрешённый run дополнительно требует `-Run -RuntimeReviewed -AcceptUnverifiedModelAndIsolation` и существующий native executable через CodexExe. RuntimeReviewed — подтверждение вызывающим ранее проверенного совместимого runtime, а не установка host и не автоматическое доказательство safety. Старые switches `--cap8` и `--forced-handoff-only` удалены. Resume использует тот же controller ledger и запускает только допустимую ещё не отправленную работу; модельную беседу он не возобновляет.

Потребитель читает `poc-exports/cap8-serial-public-toy-v2/latest.json`, разрешает relative snapshot paths внутри этого каталога, проверяет каждый SHA-256, затем читает summary и параллельные отчёты. Он должен учитывать evidence kind, collection status, stop reason, coverage и remaining budget. Schema отклоняет неожиданные поля и небезопасные значения. Exports и metadata кампании игнорируются Git; создание экспорта не публикует его. Неизменяемые snapshots и указатель допускают безопасный повторный экспорт частичных исходов.

## 6. Оставшиеся блокеры и следующий шаг

Код и offline-проверки завершены; **функциональная live-автоматизация остаётся непроверенной**. CodexSandboxOffline не наследует авторизацию CLI обычного Windows-пользователя. Controller не предоставляет перенос credentials, login, daemon, listener, queue, постоянный scheduler или мост удалённого запуска. Для будущего разрешённого live-теста всё ещё нужен запуск обычным авторизованным пользователем; dot может прочитать безопасный экспорт через уже доступный проект.

Совместимый установленный Code Mode host и effective model-selected tool mode не продемонстрированы при сохранённом изолированном argv. `--ignore-user-config` намеренно сохранён для исключения произвольных пользовательских MCP/hooks/instructions. Если доступность host зависит от исключённой этим флагом конфигурации, до dispatch нужно разрешить prerequisite поддерживаемого изолированного runtime; нельзя молча убрать ограничение, установить software или изменить security. Неизвестные startup JSON/stderr diagnostics, отсутствующий учёт и unresolved reservations останавливают дальнейшие launches, сохраняя наблюдаемые затраты. Установок, auth- и security-изменений не выполнялось.

Штатный read-only access не является read jail для hidden grader; strict secrecy, backend confirmation, per-network-request receipts и экономия подписки не заявляются. [Закреплённый tool selector](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/core/src/tools/mod.rs#L82) объясняет, почему false feature toggles не отменяют model-selected mode; [закреплённый event contract](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/exec/src/exec_events.rs#L1) определяет stage usage. [Официальные сведения о конфигурации](https://learn.chatgpt.com/docs/config-file/config-reference) дают текущий контекст, но не подтверждают версию.

Далее: проверить эти подтверждённые code/export artifacts, сохранить тот же приватный data-dir и отдельно разрешить фиксированный малый live-тест только после проверки prerequisites обычного пользовательского runtime без inference. Его первая разрешённая попытка P01 W является compatibility observation и расходует слот; бесплатного smoke test нет. Эта задача реализации/проверки не разрешает новых модельных запусков.
