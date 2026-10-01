# Architecture reports / Архитектурные отчёты

Version / Версия: **2026-10-01**

| Document / Документ | English | Русский |
|---|---|---|
| Active controller fixes and offline verification / Исправления активного controller и offline-проверки | [Verified implementation](en/controller-audit-fixes-2026-10-01.md) | [Проверенная реализация](ru/controller-audit-fixes-2026-10-01.md) |
| Complete architecture review / Полный архитектурный анализ | [Full review](en/hierarchical-llm-architecture-review-updated.md) | [Полный анализ](ru/hierarchical-llm-architecture-review-updated.md) |
| Independent conclusion and change table / Независимый вывод и таблица правок | [Independent review](en/independent-review.md) | [Независимый пересмотр](ru/independent-review.md) |
| First experiment / Первый эксперимент | [Experiment plan](en/first-experiment.md) | [План эксперимента](ru/first-experiment.md) |
| First pilot results / Результаты первого пилота | [Observed results](en/first-pilot-results.md) | [Наблюдаемые результаты](ru/first-pilot-results.md) |
| Telemetry diagnostic / Диагностика телеметрии | [Blocker and options](en/telemetry-diagnostic.md) | [Блокер и варианты](ru/telemetry-diagnostic.md) |
| Windows four-task runner / Windows runner на четырёх задачах | [Run instructions](en/windows-four-task-poc.md) | [Инструкция запуска](ru/windows-four-task-poc.md) |
| Preparation checkpoint / Контрольная точка подготовки | [Preparation only](en/preparation-checkpoint.md) | [Только подготовка](ru/preparation-checkpoint.md) |
| Economic experiment protocol / Протокол экономического эксперимента | [Current four-task subscription PoC](en/economic-experiment-protocol.md) | [Текущий подписочный PoC на четырёх задачах](ru/economic-experiment-protocol.md) |

## English

These are complete parallel editions of the architecture reassessment dated 2026-09-30. The full report preserves the economic and reliability definitions, formulas, acceptance obligations, risk register, sources, and unresolved questions. The shorter documents accompany it; they do not replace the complete report. The architecture review was a documentation-only release. A subsequently authorized, bounded model pilot is recorded separately in the pilot-results documents and shared experiment materials; no orchestrator was implemented.

### Bilingual reporting requirement

Save all subsequent project reporting documents in **both English and Russian** under `docs/en` and `docs/ru`, using matching filenames and a shared version date. Publish both language editions together. Preserve the full substantive content, section structure, formulas, constraints, qualifications, tables, and source URLs; a summary is not a substitute for a translation. Update this index and verify structural, formula, and link parity before publication. Exclude credentials, personal data not intended for publication, internal artifact identifiers, local execution paths, and transfer/debugging notes from public reports. Keep changes confined to the authorized documentation scope.

## Русский

Это полные параллельные редакции архитектурного пересмотра от 2026-09-30. Полный отчёт сохраняет определения экономики и надёжности, формулы, обязательства приёмки, реестр рисков, источники и нерешённые вопросы. Краткие документы дополняют его, а не заменяют. Архитектурный пересмотр был публикацией документации. Впоследствии разрешённый ограниченный модельный пилот описан отдельно в отчётах о результатах пилота и общих материалах эксперимента; оркестратор не реализовывался.

### Требование двуязычной отчётности

Сохраняйте все последующие отчётные документы проекта **на английском и русском языках** в `docs/en` и `docs/ru` с одинаковыми именами файлов и общей датой версии. Публикуйте обе языковые редакции вместе. Сохраняйте полное содержательное соответствие, структуру разделов, формулы, ограничения, оговорки, таблицы и URL источников; пересказ не заменяет перевод. Обновляйте этот индекс и проверяйте паритет структуры, формул и ссылок до публикации. Исключайте из публичных отчётов учётные данные, не предназначенные для публикации персональные сведения, внутренние идентификаторы артефактов, локальные пути исполнения и заметки о переносе файлов или отладке. Ограничивайте изменения разрешённым объёмом документации.
