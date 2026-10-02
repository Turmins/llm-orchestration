# Fallback каталога и нерешённый visible failure P01

Версия: 2026-10-02. Это продолжение читает safe project exports и публичные закреплённые исходники. Оно не открывает повторно private receipts, credentials или session files. Новых модельных calls этим расследованием: **0**. Третий запуск выполнил пользователь; учтённая campaign остаётся **израсходовано 3/8, осталось максимум 5**.

## Семантика timeout каталога и network evidence

Source 0.159.2 ограничивает transport/download `/models` deadline в пять секунд. Истечение deadline превращается в `RequestTimeout`. Manager перехватывает refresh error, логирует её и возвращает текущий каталог, а не передаёт ошибку завершения turn. Он начинает с bundled metadata; валидный identity-bound memory/cache catalog может её заменить. Если in-memory identity не подходит, `get_remote_models` возвращает bundled catalog. При явно указанной модели OpenAI manager сохраняет запрошенный identifier; это отличается от доступности свежей metadata или подтверждённой attribution модели backend.

Закреплённый bundled catalog включает обе модели `gpt-6-luna` и `gpt-6.1-sol` с `tool_mode=code_mode_only`. Выбор tool mode сначала использует model metadata, затем feature defaults. Поэтому свежесть каталога может влиять на локальную metadata, tool-mode configuration и instructions; discovery timeout сам по себе не доказывает неправильный ответ или незаметную замену запрошенной модели. Live catalog/cache choice, effective tool mode и actual backend model не экспортированы и остаются непроверенными. Пользовательские cache/auth files для заполнения этого пробела не читались.

Для сохранённой попытки hash-bound sidecar фиксирует process exit 0, completed stdout, полный usage, ноль runtime error events, отсутствие controller timeout и ровно одну известную stderr category: `model_catalog_refresh_request_timeout`. Исходный контроллер переводит любой непустой stderr в `stderr_diagnostic` и делает попытку непригодной даже при завершённом turn. Для этого распознанного пути исходников такое поведение — слишком широкая acceptance policy, а не доказательство сбоя native process или turn. Discovery завершилось ошибкой; turn завершился с reduced assurance. Warning/error и его затраты должны остаться учтёнными.

Источники: [deadline в пять секунд](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/model-provider/src/models_endpoint.rs), [catalog fallback и явная модель](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/models-manager/src/manager.rs), [bundled metadata](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/models-manager/models.json), [tool-mode selection](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/core/src/tools/mod.rs).

Публичный [OpenAI status summary](https://status.openai.com/api/v2/summary.json), полученный при расследовании, сообщал operational status с page timestamp 2026-09-29T18:29:41Z. Это агрегированное более раннее наблюдение не устанавливает состояние авторизованного catalog route пользователя в момент неудачного запроса. Один неавторизованный HEAD публичного ChatGPT root из executor вернул transport error без HTTP response примерно за 0.131 seconds. Он не использовал credentials и не делал model request. Это наблюдение executor не диагностирует route обычного пользователя, причину DNS/TLS/proxy/server или исторический timeout в пять секунд. Авторизованный catalog/live-model probe не выполнялся.

## Сборка P01, visible checks и точные недостающие данные

Public packet, восстановленный из неизменной frozen task, имеет 853 UTF-8 bytes и содержит instruction, все семь input intervals, visible rule, response format и task ID. Его hash совпадает с экспортированным `prompt_sha256` попытки. Source контроллера записывает тот же body до reservation и передаёт его bytes прямо в stdin. Неправильная или неполная prompt assembly не доказана. Это проверяет записанный/переданный body контроллера, а не независимый server-side echo.

Visible checker требует единственный intervals key, integer pairs, положительные длины, отсортированный порядок и неперекрывающиеся соседние интервалы; касающиеся endpoints разрешены. Он намеренно не устанавливает original coverage или final correctness. Offline cases проверяют, что результат transitive overlap и касающиеся endpoints принимаются, а malformed keys, пустые интервалы, несортированные/перекрывающиеся интервалы и boolean endpoints отклоняются. Пустой список результата может пройти structural visible check, но не пройти final coverage/correctness. JSON object сам по себе не является правильным ответом.

Сохранённый safe export сообщает JSON-object answer и visible failure, но не содержит ни hash-bound answer, ни per-check failure codes. Поэтому точное нарушенное условие остаётся неизвестным; его нельзя вывести из 22 output tokens или timeout каталога. Недостающие данные: `visible_failure_codes` либо original hash-bound candidate в явно разрешённом safe artifact. Private candidate/stdout files в этом продолжении не читались.

Postmortem producer теперь поддерживает статические P01 failure codes без экспорта keys, interval values или raw answer text. Следующее обычное пользовательское non-inference действие producer — пересоздать его safe sidecar из уже сохранённых experiment receipts, затем проверить экспортированные codes. Это действие producer не выполнялось над private receipts в данном продолжении. Пока safe codes не предоставлены, точный visible failure остаётся блокером.

Из корня проекта в обычном пользовательском терминале:

```powershell
py -3 -B -X utf8 .\docs\experiments\toy-poc-v1\inspect_export.py --data-dir (Join-Path (Split-Path (Get-Location).Path -Parent) 'LLM-PoC-cap8')
```

## Реализованный assessment, проверки и сохранённые затраты

Минимальное реализованное исправление — семантическая диагностика: `inspect_export.py --public-only` читает только исходный project export и hash-bound diagnostic sidecar. Оно распознаёт точный pinned discovery timeout только при completed stdout, exit 0, полном usage, нуле error events и отсутствии interruption/tool violation. Оно сообщает `completed_with_nonfatal_discovery_warning` и `reduced_catalog_freshness_unverified`; unknown stderr, runtime errors, tool violations или partial telemetry остаются blocking/unclassified. Записывается `poc-exports/cap8-serial-public-toy-v2/assessment-latest.json` с сохранением всех source bindings. Оно не меняет recorded usable flag ledger, blanket live-routing gate или frozen source manifest и не возобновляет campaign. Это исправление диагностической classification, а не заявленное исправление live gate или clean model success.

Десять целевых diagnostic tests проходят в обычном и оптимизированном Python, ноль failures/errors/skips. Они расширяют предыдущий suite из шести tests проверками public-only/no-private-reader behavior, совместимости при missing codes, unknown/error blocking, отклонения stale binding и правил P01. Counts не складываются: предыдущий architectural suite имеет 44 tests; первые postmortem evidence — 6; этот расширенный diagnostic suite — 10, включая те 6. Suite из 44 tests не повторялся. Доказательства: `discovery-validation-2026-10-02.json` и `discovery-validation-optimized-2026-10-02.json`. Python AST, JSON, PowerShell parser, bilingual parity, source provenance и diff checks проходят.

| Учтённая попытка | Input | Cached input | Cache-write | Output | Reasoning output | Recorded diagnostic |
|---|---:|---:|---:|---:|---:|---|
| Historical W | 7629 | 1792 | 0 | 90 | 66 | Code Mode host unavailable; exit unknown |
| Historical E | 8319 | 0 | 0 | 68 | 44 | Code Mode host unavailable; exit 0 |
| User-run P01-W-a01 | 7675 | 1792 | 0 | 22 | 0 | Catalog refresh timeout; exit 0; visible failure |

Известные input/output subtotals — 23623/180; их сумма 23803 — known subtotal, а не заявление о полной telemetry исторических partial receipts. Cache/reasoning components повторно не прибавляются. Денежные/API charge и actual model остаются неизвестными. Refund, relaunch, E takeover, перевыбор задач, изменение security/auth/install, публикация raw logs и merge не выполнялись. Точный P01 failure и live catalog/network cause остаются нерешёнными; изменение bound live policy отложено до проверяемости этих фактов и поведения reduced assurance.
