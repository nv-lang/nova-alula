# Журнал языка: таблица шаблонов кодов Алулы

Коды журнала, которые пишет сам язык: формат (5), библиотека «Пауза» (8), движок и исполнитель (22), всего 35 (спецификация, раздел 7а, AL-113). Хозяин их не переопределяет: таблица хозяина (`journal.md` рядом с его машинами) не повторяет ни одного из этих кодов. Форма: `Машина | Код события | Русский шаблон | Параметры`. Файл читает `journal.nv`.

| Машина | Код события | Русский шаблон | Параметры |
|---|---|---|---|
| формат | `signal_passed` | {signal} передан {request} | `signal`, `request` |
| движок | `human_stop` | стоп человека: {author}, {source}, запись {event} | `author`, `source`, `event` |
| движок | `pause_by_parent_stop` | пауза: причина — стоп от родителя, {request}, запись {event} | `request`, `event` |
| движок | `cancel_discarded_foreign_request` | отмена отброшена: чужой запрос {request}, запись {event} | `request`, `event` |
| движок | `cancel_discarded_already_replied` | отмена отброшена: ответ уже отдан, {request}, запись {event} | `request`, `event` |
| движок | `request_cancelled` | отмена запроса: {request}, запись {event} | `request`, `event` |
| движок | `cancel_parse_no_match` | ошибка машины: разбор отмены_запроса, ни одно условие не подошло | — |
| движок | `human_continue` | продолжение с {previous}: {author}, {source}, запись {event} | `previous`, `author`, `source`, `event` |
| движок | `parent_continue` | продолжение с {previous}: от родителя {request}, запись {event} | `previous`, `request`, `event` |
| шаг агента, раннер, проверка, сессия, совещание | `fork_no_match` | ошибка машины: развилка {fork}, ни одно условие не подошло | `fork` |
| шаг агента, раннер, проверка, сессия, совещание | `machine_data` | данные машины: {data} | `data` |
| шаг агента, раннер, проверка, сессия, совещание | `machine_error` | ошибка машины: {reason} | `reason` |
| шаг агента, раннер, проверка, сессия, совещание | `input_rejected` | вход отклонён: {reason}; поле {field}; инвариант {index} | `reason`; необязательные `field`, `index` |
| движок | `machine_started` | машина запущена: {machine} | `machine` |
| движок | `event_accepted` | принято событие {name} ({kind}); источник {source}; вход {input} | `kind`, `name`; необязательные `source`, `input` |
| движок | `reply_discarded` | ответ отброшен: {reason} | `reason` |
| движок | `request_ordered` | заказан запрос стороны {party}, попытка {attempt} | `party`, `attempt` |
| движок | `request_sent` | запрос отправлен, попытка {attempt} | `attempt` |
| движок | `request_repeated` | запрос отправлен снова, попытка {attempt} | `attempt` |
| движок | `request_closed` | запрос закрыт: {how}; код {code} | `how`; необязательные `code` |
| движок | `cancel_ordered` | заказана отмена запроса: {reason} | `reason` |
| движок | `cancel_sent` | отмена отправлена | — |
| движок | `cancel_without_request` | отмена стороны {party}, открытого запроса нет | `party` |
| движок | `snapshot_ordered` | заказан снимок состояния, шаг {step} | `step` |
| движок | `machine_finished` | машина закончена: {outcome}; код {code} | `outcome`, `code` |
| движок | `engine_resumed` | движок поднят из снимка: шаг {snapshot_step}, открытых {open}, не отправлено {not_sent}, отброшено строк {ignored_lines} | `snapshot_step`, `open`, `not_sent`, `ignored_lines` |
| движок | `signal_ordered` | заказан сигнал {signal} запросу {request} | `signal`, `request` |
| исполнитель | `machine_defect` | дефект машины: {kind}: {message} | `kind`, `message` |
| исполнитель | `event_ignored` | событие {event} в состоянии {state} отброшено | `event`, `state` |
| исполнитель | `event_unknown` | событие {name} машине не известно | `name` |
| исполнитель | `event_malformed` | событие {name} не читается | `name` |
| исполнитель | `answer_held` | ответ запроса {request} получен в состоянии {state}, которое его не ждёт: удержан до возврата в обращение | `request`, `state` |
| исполнитель | `answer_replayed` | удержанный ответ запроса {request} принят после возврата в обращение | `request` |
| исполнитель | `answer_edited` | ответ стороны {party} не принят: объект правки изменился, запрос {request} | `party`, `request` |
| исполнитель | `form_returned` | ответ стороны {party} возвращён по форме: возврат {returns}, запрос {request} | `party`, `returns`, `request` |
