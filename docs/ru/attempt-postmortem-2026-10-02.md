# Первая попытка исправленного контроллера: postmortem

Версия: 2026-10-02. Пользователь один раз запустил исправленный контроллер. Это расследование не делало модельных calls, не повторяло прогон и сохранило реальный бюджет **израсходовано 3/8, осталось 5**. Попытка остаётся учтённой и непригодной.

## Наблюдаемая первичная причина и затраты

Исходный project export прошёл проверки pointer schema, snapshot hashes и summary schema. Он сообщает `attempt_not_usable`, поскольку у `P01-W-a01` статус `stderr_diagnostic`. Этот статус — acceptance gate, а не первичная причина stderr. Исходный export не содержал telemetry errors, категории stderr, счётчики error events и timeout/launch-error flags; эти недостающие поля были названы до просмотра дополнительных данных эксперимента.

Структурированный ledger указанного каталога эксперимента и receipts с совпадающими hashes устанавливают первичную diagnostic: путь закреплённого `codex_models_manager::manager` записал ошибку обновления каталога моделей с `request timed out`. Это timeout discovery каталога; он не свидетельствует о disabled host. Обычная причина timeout в code/configuration не доказана. [Закреплённая обработка обновления каталога](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/models-manager/src/manager.rs).

| Наблюдение | Значение |
|---|---|
| Native process | exit 0; elapsed 17.279606900003273 seconds |
| Timeout/interruption контроллера; launch error | false; отсутствует |
| Runtime stdout и telemetry | completed; parser/accounting errors отсутствуют |
| Error events | error 0; turn.failed 0; item.error 0 |
| Usage coverage | reported_complete_stage |
| Израсходованные input; output | 7675; 22; input плюс output 7697 |
| Cached input; cache-write; reasoning output | 1792; 0; 0 |
| Acceptance ответа | JSON object; visible contract failed; independently computed correctness false в исходном summary |
| Actual model; isolation | не проверена; не проверена |

Cached input входит в input и повторно не прибавляется. Полный usage и process exit 0 не делают попытку чистым runtime success. Непрохождение visible contract JSON-объектом ответа — отдельный результат; hidden grading не передавался контроллеру и не использовался для выбора другой задачи. После остановки runtime gate не выполнялись E takeover или оставшиеся задачи.

## Реализованное исправление диагностики и tests

Подтверждённый дефект проекта — недостаточная диагностическая projection. Новый `inspect_export.py` создаёт отдельный безопасный postmortem sidecar, сохраняя frozen controller files, ledger manifest, исходный export и receipts. Он проверяет project pointer и все snapshot hashes, привязывает указанный каталог через существующий campaign owner hash, проверяет event chain ledger и provenance rows/sources, повторно разбирает stdout/stderr receipts с совпавшими hashes. Записываются только статические diagnostic codes, error-event counts, числовые usage/process fields и acceptance flags. Неизвестные строки stderr остаются помеченными `unclassified_stderr`; распознанный timeout не скрывает другие строки. Raw logs, содержимое ответа, сообщения, account identifiers и приватные пути исключены.

Дополнительный consumer entry — `poc-exports/cap8-serial-public-toy-v2/diagnostic-latest.json`; hash указанного JSON должен проверяться. Он дополнительно привязан к hash исходного summary. Изменение ledger/pointer во время проверки, подмена receipt, unsafe pointer path, неверный каталог или невалидный event chain останавливают публикацию. Runtime diagnostics не понижаются и не игнорируются, slot ledger не возвращается. Helper не создаёт subprocesses и не инициализирует ledger.

Шесть целевых offline regressions прошли в обычном и оптимизированном Python, ноль failures/errors/skips: сохранение затрат/process status и исключение private data; подмена receipt с сохранением прежней diagnostic; повреждение snapshot и traversal; directory binding и ledger chain; malformed JSONL с сохранением usage/error counts; отклонение небезопасной process metadata. Глобальный subprocess guard запрещает все subprocesses в этих tests. Доказательства: `postmortem-validation-2026-10-02.json` и `postmortem-validation-optimized-2026-10-02.json`. PowerShell parser, Python AST, strict JSON, bilingual parity и diff checks прошли. Завершённый архитектурный suite из 44 tests не повторялся и не переписывался.

## Сохранённое состояние и оставшийся блокер

Безопасный sidecar создан автоматически из сохранённых receipts, без ручного копирования raw logs. Ledger, оба raw receipts и исходный pointer сохранили hashes; исходный summary остаётся остановленным на **3/8**, с **5** оставшимися slots. Существующие незакоммиченные файлы сохранены. В существующую draft PR публикуются только diagnostic code/tests, их безопасные доказательства и двуязычный отчёт; merge и публикация private logs не выполнялись.

Timeout запроса каталога моделей остаётся нерешённым. Имеющиеся доказательства не устанавливают его network/server/configuration cause, effective live model или tool mode. Следующий шаг — поддерживаемая non-inference диагностика каталога/runtime в обычной авторизованной пользовательской среде. Нельзя повторять модельный прогон, игнорировать stderr, менять auth/security/install settings или мигрировать/сбрасывать привязанный ledger ради дополнительных slots. Эта правка улучшает диагностику уже израсходованной попытки; она не заявляет исправленный live runtime.
