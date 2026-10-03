# Оркестрация Codex без ПК пользователя

Дата: 2026-10-03  
Статус: исследование документации и открытых исходников; выполнение в облаке не подтверждено

## Вывод

Для этого публичного репозитория самый простой поддерживаемый первый шаг — обычная задача Codex Cloud с входом через ChatGPT. Codex Cloud может работать, пока ПК пользователя спит. Запуск собственного вложенного CLI-оркестратора проекта внутри такой задачи — отдельный вопрос совместимости, который пока не проверен. [Codex Cloud](https://learn.chatgpt.com/docs/cloud), [аутентификация](https://learn.chatgpt.com/docs/auth)

Постоянно доступный runner на сервере пользователя — другая архитектура. Вход через ChatGPT на headless-сервере описан, но расширенное руководство по account-auth для CI прямо исключает процессы с публичными/open-source репозиториями. Наличие частной VM или вручную выбранного checkout не подтверждает исключение из этого ограничения. [Headless-вход](https://learn.chatgpt.com/docs/auth#login-on-headless-devices), [расширенная аутентификация CI](https://learn.chatgpt.com/docs/auth/ci-cd-auth)

## Доказательства и границы исследования

В этом обзоре прочитаны официальная документация и публичные исходники OpenAI Codex. Код репозитория не запускался; inference, создание сервисов, доступ к ПК пользователя и перенос учётных данных не выполнялись.

Предоставленная контрольная точка проекта за 3 октября сообщает:

- Задача безопасно завершила собственные командные сессии; отсутствие процессов во всей системе не установлено
- В бюджете запусков проекта использовано 3 из лимита 8; осталось не более 5
- Нового inference и запусков тестов не было
- Журнал из шести событий и его хеш не изменились
- Незакоммиченное частичное изменение политики в cli_runner.py не проверено тестами и должно быть сохранено

Это наблюдения из предоставленной контрольной точки, а не результаты, повторно полученные в ходе данного исследования документации. Текущая проверка облачного runtime была недоступна. Последний безопасный диагностический экспорт установил adjacent_intervals_overlap как visible failure P01; пять ранее выполненных граничных проверок подтвердили корректность checker. Эти данные заменяют прежнее утверждение отчёта о неизвестной причине failure. Локальная частичная правка политики не входит в проверенный удалённый код.

Локально установленный CLI указан как 0.159.2; историческая попытка в управляемом облаке использовала 0.159.0-alpha.3. Соответствующие публичные release-коммиты: ff6aec96948b70d94983af2641a6b67c94faeff5 и 3b01b36fa5eb96ba82a776bd3c2fc57f8969181f. Отдельно изучены текущие исходники main на [b741e480e203f037ca726bc2a76d99a8e8668e66](https://github.com/openai/codex/commit/b741e480e203f037ca726bc2a76d99a8e8668e66). Поведение исходников не доказывает идентичное поведение установленного бинарника или управляемого хоста. [Релиз 0.159.2](https://github.com/openai/codex/releases/tag/rust-v0.159.2), [релиз alpha.3](https://github.com/openai/codex/releases/tag/rust-v0.159.0-alpha.3)

## Доступные архитектуры

### Управляемый Codex Cloud

Опубликованная среда задаёт подготовленную файловую систему; каждая новая задача получает изолированное рабочее пространство. Повторное открытие той же задачи сохраняет её файлы, включая незакоммиченные изменения и установленные инструменты. По умолчанию состояние VM можно восстановить в течение семи дней после последнего хода или возобновления. Это сохранение состояния задачи, а не документированная гарантия постоянно работающего сервиса. Важные результаты следует сохранять в системе контроля версий. [Облачные среды](https://learn.chatgpt.com/docs/environments/cloud-environments)

Старое руководство по cloud environment теперь относится к legacy-режиму. Его двенадцатичасовой срок кеширования контейнера нельзя подставлять вместо текущего правила хранения состояния задачи. [Legacy-облачные среды](https://learn.chatgpt.com/docs/environments/cloud-environment)

### Удалённый CLI на сервере пользователя

Удалённый/headless-хост может использовать codex login --device-auth после включения device-code входа для аккаунта или workspace. Пользователь всё равно подтверждает вход в браузере. codex exec использует сохранённую аутентификацию. Вход подтверждает идентичность аккаунта, но не доступ ко всем моделям и не бессрочную автономную работу. [Аутентификация](https://learn.chatgpt.com/docs/auth), [неинтерактивный режим](https://learn.chatgpt.com/docs/non-interactive-mode)

Для доверенной частной автоматизации account-auth руководство требует сохранять обновлённое состояние входа и использовать одну машину либо последовательный поток jobs на одну копию auth.json. Для обычного CI рекомендованы API-ключи; этот процесс запрещён для публичных/open-source репозиториев. В публичном CI данного репозитория применять его не следует. [Расширенная аутентификация CI](https://learn.chatgpt.com/docs/auth/ci-cd-auth)

Доступность runner, хранение данных, управление процессами и эксплуатационные расходы потребуют отдельно выбранного хостинга. В этом исследовании такой хостинг не создавался и не проверялся.

### Отдельные варианты интеграции с подпиской

Официальная документация Sign in with ChatGPT описывает OAuth-доступ к использованию плана для open-source/локально размещённых приложений и процедуру для self-hosted VM. Это отдельная архитектура регистрации клиента и согласия пользователя, а не обход ограничений с помощью скопированных CLI-credentials. Для платных или удалённо размещённых приложений предусмотрена отдельная процедура выражения интереса. [Обзор plan usage](https://developers.openai.com/siwc/token-sharing-open-source), [self-hosted VM](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms)

Интеграция с Codex App Server требует, чтобы приложение управляло обновлением токена. Preview-запросы требуют streaming и store:false; часть полей Responses и hosted tools не поддерживается. Локальная история и resume доступны. Совместимость с этим проектом и аккаунтом не проверена. [Интеграция App Server](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server), [preview-ограничения](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)

Codex access tokens документированы для Business и Enterprise workspace. Workload identity federation для Codex — beta, которую включают для workspace. Нельзя считать эти возможности доступными в неуточнённой личной подписке. [Access tokens](https://learn.chatgpt.com/docs/enterprise/access-tokens), [workload identity federation](https://developers.openai.com/api/docs/guides/workload-identity-federation)

Self-hosted executor Agents API использует API-ключи приложения и среды. Его документация не описывает превращение обычного ChatGPT-входа CLI в доступ к Agents API за счёт подписки. [Self-hosted sandbox API](https://developers.openai.com/api/docs/guides/agents-api/environments/self-hosted)

## Записываемое состояние runtime и историческая ошибка

В исторической попытке alpha.3 был указан вход через ChatGPT, но запуск внутреннего App Server завершился ошибкой read-only filesystem. Это подтверждает блокер запуска, а не успешный inference и не доказанную причину проблем со всеми путями состояния.

Codex документирует CODEX_HOME для config, auth, logs и sessions, а CODEX_SQLITE_HOME — для SQLite-состояния; явно заданный sqlite_home имеет приоритет. Каталог заданного CODEX_HOME должен уже существовать. [Переменные окружения](https://learn.chatgpt.com/docs/config-file/environment-variables), [справочник конфигурации](https://learn.chatgpt.com/docs/config-file/config-reference)

Оба release-исходника выбирают SQLite-хранилище в порядке sqlite_home, CODEX_SQLITE_HOME, CODEX_HOME. Runtime создаёт каталог, открывает и мигрирует несколько баз; записываемые SQLite-соединения используют WAL. Поэтому важны права на запись каталога и вспомогательных файлов. [Разрешение путей 0.159.2](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/config/mod.rs#L4059-L4076), [разрешение путей alpha.3](https://github.com/openai/codex/blob/3b01b36fa5eb96ba82a776bd3c2fc57f8969181f/codex-rs/core/src/config/mod.rs#L4058-L4075), [инициализация runtime](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/state/src/runtime.rs#L103-L196), [записываемое SQLite-соединение](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/state/src/sqlite.rs#L296-L311)

Вариант для проверки: разместить состояние дочернего CLI в явно разрешённых записываемых каталогах, отдельно от checkout и состояния управляемого родительского процесса. Это гипотеза конфигурации. Её успешность против исторической ошибки не проверена. Перенос пути хранения не отменяет обязательные ограничения доступа; нельзя считать, что новый CODEX_HOME унаследует вход.

## Сохранение состояния и границы безопасности

codex exec поддерживает возобновление сохранённой сессии; --ephemeral отключает сохранение session rollout. Для постоянной истории нужно долговечное хранилище состояния независимо от checkout репозитория. [Неинтерактивный режим](https://learn.chatgpt.com/docs/non-interactive-mode)

Режим read-only для команд агента не означает, что сам CLI не пишет состояние runtime. Учётные данные не должны попадать в публичный репозиторий, артефакты и логи. Файловый auth — кеш access tokens, который нужно защищать как пароль. [Расширенная конфигурация](https://learn.chatgpt.com/docs/config-file/config-advanced#config-and-state-locations), [хранение credentials](https://learn.chatgpt.com/docs/auth#credential-storage)

Для будущей собственной интеграции предпочтителен локальный stdio. Текущая документация App Server называет WebSocket-транспорт experimental/unsupported и предупреждает: non-loopback listener по умолчанию может принимать неаутентифицированные подключения, пока явно не настроена транспортная аутентификация. Открытие управляющего порта runner не должно быть сокращённым путём настройки. [Транспорт App Server](https://learn.chatgpt.com/docs/app-server#protocol)

Sandbox и approval policy — отдельные механизмы; отключение подтверждений не создаёт отсутствующее право записи. Будущая проверка должна использовать минимально необходимые права без широкого full-access escalation. [Подтверждения и безопасность агента](https://learn.chatgpt.com/docs/agent-approvals-security)

## Учёт JSONL usage и идентичность модели

1. codex exec --json выдаёт JSONL-события. Успешное финальное событие содержит usage. Следует сохранить полный поток и stderr приватно, затем подготовить очищенную сводку. [Неинтерактивный вывод](https://learn.chatgpt.com/docs/non-interactive-mode#make-output-machine-readable)
2. В схемах обоих исследованных релизов есть input_tokens, cached_input_tokens, cache_write_input_tokens, output_tokens и reasoning_output_tokens. Парсер должен сохранять доступные поля и различать отсутствующее значение и ноль. [Схема 0.159.2](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/exec/src/exec_events.rs#L59-L73), [схема alpha.3](https://github.com/openai/codex/blob/3b01b36fa5eb96ba82a776bd3c2fc57f8969181f/codex-rs/exec/src/exec_events.rs#L59-L73)
3. Обработчик копирует накопительное thread tokenUsage.total в turn.completed.usage. У свежего одноходового thread нет предыдущего baseline; это соответствует предоставленному описанию проекта, где на каждый этап создаётся новый thread. Двойной учёт в текущем журнале не установлен. Для resumed thread нужен проверенный cumulative baseline/delta; нельзя просто суммировать финальные totals. [Обработчик 0.159.2](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L118-L128), [обработчик alpha.3](https://github.com/openai/codex/blob/3b01b36fa5eb96ba82a776bd3c2fc57f8969181f/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L509-L565)
4. При failed/interrupted запуске финального usage может не быть; отсутствие обновлений может дать нули по умолчанию. Отсутствующая/нулевая телеметрия не доказывает отсутствие расхода. Следует отмечать неполный учёт и консервативно сохранять резерв бюджета. [Обработка финальных событий](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L509-L565)
5. Запрошенную модель, provider, reasoning effort, speed mode, версию бинарника, статус результата и наблюдаемые reroutes нужно записывать отдельно. Обычный exec thread.started сообщает идентификатор thread, но не доказывает модель, обслужившую запрос. Reroute выводится как текст item типа error. [Модельные события exec](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L494-L535)
6. Cached input входит в input; reasoning output входит в output. Повторно прибавлять эти детализации нельзя. Cache-write, если он есть, следует хранить отдельно и не выводить из него стоимость подписки. [Преобразование upstream usage](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/codex-api/src/sse/responses.rs#L117-L155), [категории токенов](https://developers.openai.com/api/docs/guides/agents-api/observability#understand-token-usage)
7. App Server предоставляет структурированный usage с идентификаторами thread/turn, накопительным total и last; last — последний ответ модели, а не весь ход с несколькими ответами. Для возобновляемой интеграции следует фиксировать baseline после resume и вычислять дельты хода. Структурированные поля reroute улучшают атрибуцию, но не доказывают точный backend snapshot модели. [Протокол usage](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/app-server-protocol/src/protocol/v2/thread.rs#L1875-L1965), [накопление счётчиков](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/protocol/src/protocol.rs#L2275-L2314), [протокол reroute](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/app-server-protocol/src/protocol/v2/model.rs#L185-L194)
8. Заголовки с server-reported моделью обрабатываются внутри клиента. Исследованный helper несовпадения назначает фиксированную причину reroute, поэтому по ней одной нельзя установить реальную причину политики. Каталог моделей не подтверждает entitlement. [Обработка заголовков модели](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/codex-api/src/sse/responses.rs#L49-L76), [обработка несовпадения](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/session/mod.rs#L4028-L4065), [ограничение каталога](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server)

Телеметрия токенов, число запусков проекта и остаток подписки — разные измерения. Локальная и облачная работа используют общий лимит плана; расход зависит от модели, контекста, инструментов, reasoning и кеширования. Фактические лимиты и время сброса нужно проверять в usage dashboard. В этом обзоре не установлена формула преобразования токенов в квоту подписки или стоимость API. [Тарифы и лимиты](https://learn.chatgpt.com/docs/pricing)

## Рекомендация и минимальная будущая проверка

Рекомендация: сначала восстановить доступ к сохранённой управляемой среде Codex Cloud. Для публичного репозитория использовать обычные облачные задачи. После этого отдельно проверить, способен ли собственный CLI-оркестратор проекта работать внутри разрешённых границ runtime. Постоянный daemon и новая OAuth-архитектура не нужны до получения базового результата совместимости.

Предлагаемая следующая проверка не выполнялась в этом исследовании документации. Новый хостинг, выдача доступа и изменения безопасности требуют соответствующего согласования:

1. До любых изменений сохранить незакоммиченную частичную правку. Начать с чистого согласованного cloud checkout и записать точные версии CLI и дочернего App Server
2. Выполнить preflight без inference: проверить действующую конфигурацию и разрешённые каталоги состояния, инициализировать изолированный stdio App Server без запуска модельного хода. Успех — завершённая инициализация и корректное закрытие без ошибок записи состояния
3. Если preflight успешен и аутентификация доступна через поддерживаемый, одобренный пользователем процесс, сначала подтвердить доступ к единому журналу кампании без его сброса или дублирования, затем зарезервировать не более одного дополнительного запуска проекта и выполнить маленький read-only prompt в новом thread
4. Требовать exit status, успешное финальное событие, корректный JSONL, явную оценку полноты usage и доказательства requested-versus-observed модели. Отдельно указать неопределённость маршрутизации. Журнал проекта и usage dashboard проверять раздельно
5. Остановиться после одного запуска или первого блокера. Не повторять inference автоматически, не расширять права, не копировать управляемые credentials и не перезаписывать сохранённую локальную частичную правку

Это ограниченный план проверки, а не утверждение, что cloud runner уже работает. Ошибка до inference оставляет совместимость неустановленной; успешный одиночный ход ещё не доказывает обновление токенов, resume, конкурентное выполнение и надёжность постоянно работающего сервиса.

