# Журнал: таблицы шаблонов методики

Копия данными двух таблиц файла `state-machines/state-machine-journal.md` методики (коммит `255fe28`, чужой репозиторий, только чтение): раздел 2 «Таблица шаблонов» и подраздел «События формата таблиц». Форма та же: `Машина | Код события | Русский шаблон | Параметры`. Это коды методики; коды продукта лежат рядом, в `journal_product.md` (формат Алулы 2.12, раздел 5, AL-31). Файл читает `journal.nv`; правится только вслед за методикой.

| Машина | Код события | Русский шаблон | Параметры |
|---|---|---|---|
| движок | `signal_passed` | {signal} передан {request} | `signal`, `request` |
| движок | `human_stop` | стоп человека: {author}, {source}, запись {event} | `author`, `source`, `event` |
| движок | `pause_by_parent_stop` | пауза: причина — стоп от родителя, {request}, запись {event} | `request`, `event` |
| движок | `cancel_discarded_foreign_request` | отмена отброшена: чужой запрос {request}, запись {event} | `request`, `event` |
| движок | `cancel_discarded_already_replied` | отмена отброшена: ответ уже отдан, {request}, запись {event} | `request`, `event` |
| движок | `request_cancelled` | отмена запроса: {request}, запись {event} | `request`, `event` |
| движок | `cancel_parse_no_match` | ошибка машины: разбор отмены_запроса, ни одно условие не подошло | — |
| движок | `human_continue` | продолжение с {previous}: {author}, {source}, запись {event} | `previous`, `author`, `source`, `event` |
| движок | `parent_continue` | продолжение с {previous}: от родителя {request}, запись {event} | `previous`, `request`, `event` |
| шаг агента | `turn_requests_exhausted` | агент исчерпал предел запросов хода | — |
| шаг агента | `model_refused` | модель отказалась отвечать | — |
| шаг агента | `turn_cancelled` | ход агента отменён | — |
| шаг агента | `agent_permanent_error` | постоянная ошибка агента | — |
| шаг агента | `turn_failed` | ход агента не состоялся: {reason} | `reason` |
| шаг агента | `agent_transient_error` | временная ошибка агента: повтор {retry} | `retry` |
| шаг агента | `agent_transient_error_exhausted` | временная ошибка агента не прошла после {retries} повторов | `retries` |
| шаг агента, раннер, проверка, сессия, совещание | `fork_no_match` | ошибка машины: развилка {fork}, ни одно условие не подошло | `fork` |
| шаг агента | `output_truncated_continue` | выход обрезан: ход «продолжи с места обрыва» | — |
| шаг агента | `output_truncated_again` | выход обрезан повторно: предел токенов | — |
| шаг агента | `agent_no_result` | агент не дал результата | — |
| шаг агента | `reply_form_violated` | форма ответа нарушена: ход «исправь форму файла» | — |
| шаг агента | `reply_form_not_fixed` | форма ответа не исправлена со второй попытки | — |
| шаг агента | `permission_auto_allowed` | разрешение: {action} — разрешено политикой автоматически | `action` |
| шаг агента | `permission_auto_denied` | разрешение: {action} — отказано политикой автоматически | `action` |
| шаг агента | `permission_human_allowed` | разрешение: {action} — человек разрешил | `action` |
| шаг агента | `permission_human_denied` | разрешение: {action} — человек отказал | `action` |
| шаг агента | `token_limit` | предел токенов исчерпан: израсходовано {spent} | `spent` |
| шаг агента | `cost_limit` | предел стоимости исчерпан: израсходовано {spent} | `spent` |
| шаг агента | `turn_limit` | предел ходов исчерпан: отправлено {sent} | `sent` |
| шаг агента | `agent_step_stopped` | шаг агента остановлен: {reason} | `reason` |
| шаг агента | `agent_usage` | расход агента: сессия {session}, результат {result}, модель {model}, токены вход {input}, выход {output}, рассуждение {reasoning}, кэш чтение {cache_read}, кэш запись {cache_write}, стоимость {cost}; «нет» — транспорт значения не дал | `session`, `result`, `model`, `input`, `output`, `reasoning`, `cache_read`, `cache_write`, `cost` |
| раннер | `edit_after_approval_specification` | правка после утверждения, статус снят: спецификация | — |
| раннер | `brief_copy_edit_after_approval` | правка копии постановки после утверждения, статус снят: спецификация | — |
| раннер | `edit_after_approval_plan` | правка после утверждения, статус снят: план | — |
| раннер, проверка | `session_launch_failed` | запуск сессии {session} не дал итога: {reason} | `session`, `reason` |
| раннер | `route_proposed` | маршрут предложен: {proposal}, {source}: {basis} | `proposal`, `source`, `basis` |
| раннер | `factory_word_missing` | слово завода не названо: быстрый маршрут не принят, ворота Gate14 повторяются | — |
| раннер | `factory_word_date_missing` | дата слова завода не названа: быстрый маршрут не принят, ворота Gate14 повторяются | — |
| раннер | `full_route_settings_rejected` | настройки полного маршрута отклонены: {reason} | `reason` |
| раннер | `fast_route_settings_rejected` | настройки быстрого маршрута отклонены: {reason}, возврат на полный маршрут | `reason` |
| раннер | `route_recorded` | маршрут записан: {route}, {source}: {basis} | `route`, `source`, `basis` |
| раннер | `fast_route_brief_incomplete` | быстрый маршрут: постановка неполна, нужны критерии `AC-N` и строка `Ветка:` | — |
| раннер | `brief_copy_created` | копия постановки создана как спецификация: {factory_word} | `factory_word` |
| раннер | `full_route_return` | возврат на полный маршрут: {source}: {basis} | `source`, `basis` |
| раннер | `foreign_approval_cleared` | чужое утверждение снято: {document} | `document` |
| раннер | `fast_route_copy_approved` | быстрый маршрут: копия постановки утверждена словом завода, С1, С2, Gate4 и Gate5 пропущены | — |
| раннер | `fast_route_copy_edited` | быстрый маршрут: копию правили после утверждения, нужно новое слово человека | — |
| раннер | `fast_route_no_brief` | быстрый маршрут: постановки нет | — |
| раннер | `fast_route_requirements_fix_queue` | быстрый маршрут: очередь правки требований | — |
| раннер | `review_parsing_failed` | проверка разбора не дала итога: {reason} | `reason` |
| раннер | `fast_route_plan_phase_skipped` | быстрый маршрут: фаза PlanPhase пропущена, план реализации — в начале отчёта реализации | — |
| раннер | `fast_route_plan_fix_queue` | быстрый маршрут: очередь правки плана | — |
| раннер | `plan_review_failed` | проверка плана не дала итога: {reason} | `reason` |
| раннер | `default_confirmed` | умолчание подтверждено | — |
| раннер | `review_restart_outside_delivery` | ошибка машины: проверка реализации вернула «перезапуск», который бывает только у сдачи | — |
| раннер | `implementation_review_failed` | проверка реализации не дала итога: {reason} | `reason` |
| раннер | `delivery_review_failed` | проверка сдачи не дала итога: {reason} | `reason` |
| раннер | `delivery_no_code_changes` | сдача без изменений кода | — |
| раннер | `runner_stopped` | раннер остановлен: {reason} | `reason` |
| раннер | `task_completed` | задача завершена, раундов обратной связи: {feedback_rounds} | `feedback_rounds` |
| проверка | `clean_needed_below_min` | ошибка машины: чистых_подряд ниже минимума методики | — |
| проверка | `probes_min_below_min` | ошибка машины: проб_в_чистом ниже минимума методики | — |
| проверка, совещание | `meeting_stopped` | совещание остановлено: {reason} | `reason` |
| проверка | `no_summary_line_all_significant` | итоговой строки нет, все находки считаются существенными | — |
| проверка, совещание | `pass_clean_without_probes` | заход {pass}: чистый без проб, не засчитан | `pass` |
| проверка, совещание | `pass_probes_not_probes` | заход {pass}: пробы — не пробы, не засчитан | `pass` |
| проверка | `owner_narrowed` | решение владельца: сужено: {loss} | `loss` |
| проверка | `review_stopped` | проверка цикла остановлена: {reason} | `reason` |
| проверка | `review_state` | проверка цикла: вердикт {verdict}, источник {source}, номер_захода {pass}, заход_отсчёта {origin}, серия_чистых {streak}, без_проб_подряд {no_probes}, записей сужено {narrowed} | `verdict`, `source`, `pass`, `origin`, `streak`, `no_probes`, `narrowed` |
| сессия | `session_not_finished` | сессия {session} не завершилась: {reason} | `session`, `reason` |
| сессия | `session_launch_stopped` | запуск сессии остановлен: {reason} | `reason` |
| сессия | `session_result` | запуск сессии: сессия {session}, итог {outcome} | `session`, `outcome` |
| совещание | `witness_no_answer` | СВИДЕТЕЛЬ не ответил: {reason} | `reason` |
| совещание | `lens_no_answer` | линза {party} не ответила: {reason} | `party`, `reason` |
| совещание | `lens_dropped` | линза {party} отброшена в заходе {pass} | `party`, `pass` |
| совещание | `no_summary_line` | итоговой строки нет | — |
| совещание | `author_fix_no_answer` | ПРАВКА: автор не ответил: {reason} | `reason` |
| совещание | `author_question_no_answer` | ВОПРОС: автор не ответил: {reason} | `reason` |
| совещание | `copy_restore_no_copy` | ВОЗВРАТ: копии нет | — |
| совещание | `older_findings_in_pass_files` | значимые находки прежних заходов, не вошедшие в «открыто», — в файлах заходов | — |

| Машина | Код события | Русский шаблон | Параметры |
|---|---|---|---|
| шаг агента, раннер, проверка, сессия, совещание | `machine_data` | данные машины: {data} | `data` |
| шаг агента, раннер, проверка, сессия, совещание | `machine_error` | ошибка машины: {reason} | `reason` |
| шаг агента, раннер, проверка, сессия, совещание | `input_rejected` | вход отклонён: {reason}; поле {field}; инвариант {index} | `reason`; необязательные `field`, `index` |
| совещание | `unclosed_finding` | незакрытая находка: {severity}, {evidence}, повтор {repeat}, вопрос {question} | `severity`, `evidence`, `repeat`, `question` |
| совещание | `meeting_decision` | решение совещания: {decision}, источник {source}, заходов {passes} | `decision`, `source`, `passes` |
| совещание | `open_finding` | открыто: {severity}, {evidence}, повтор {repeat}, вопрос {question} | `severity`, `evidence`, `repeat`, `question` |
